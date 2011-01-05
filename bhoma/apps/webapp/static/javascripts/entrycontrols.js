/* === INHERITANCE PATTERN === */

function inherit (subclass, superclass) {
  subclass._super = superclass._super || {};
  for (var e in superclass) {
    if (e != '_super' && e != 'super') {
      if (typeof(superclass[e]) != 'function') {
        subclass[e] = superclass[e];
      } else {
        if (subclass._super[e] == null) {
          subclass._super[e] = [];
        }
        subclass._super[e].push(superclass[e]);
        subclass[e] = passToParent(e);
      }
    }
  }
  subclass.super = function (funcName) {
    return invokeSuper(this, funcName);
  }
}

function passToParent (funcName) {
  return function () {
    return this.super(funcName).apply(null, arguments);
  }
}

function invokeSuper (self, funcName) {
  return function () {
    var basefunc = self._super[funcName].pop();
    if (!basefunc) {
      throw new Error('function ' + funcName + ' not defined in superclass');
    }
    var retval = basefunc.apply(self, arguments);
    self._super[funcName].push(basefunc);
    return retval;
  }
}

/* TO USE:
 *
 * early in the constructor of the child class, call:
 *   inherit(this, new SuperClass(...));
 * this is akin to calling super(...); inside a java constructor
 *
 * this call will load all variables and functions from the parent class
 * into this class.
 *
 * add additional variables and methods after the inherit() call. to
 * overload a method in the parent class, simply redefine the function
 * in this class
 *
 * to call a parent method explicitly, do:
 *   this.super('someMethod')(args);
 * this is akin to calling super.someMethod(args); in java
 */

/* ============================= */


function Entry () {
  this.help = function () {
    overlay.activate({
        text: activeQuestion["help"] || "There is no help text for this question.",
        color: HELP_BGCOLOR,
        timeout: 15.
      });
  }

  this.clear = function () {
    this.setAnswer(null, true);
  }
}

function SimpleEntry () {
  inherit(this, new Entry());

  this.next = function () {
    if (this.prevalidate()) {
      answerQuestion();
    }
  }

  this.prevalidate = function () {
    return true;
  }

  this.back = function () {
    prevQuestion();
  }
}

function FreeTextEntry (args) {
  inherit(this, new SimpleEntry());

  args = args || {};
  this.domain = args.domain || 'full';
  this.length_limit = args.length_limit || 500;

  this.inputfield = null;
  this.default_answer = null;

  this.load = function () {
    questionEntry.update(freeEntry);
    var answerBarControls = this.getAnswerBar();
    answerBarControls.inputfield.setMaxLen(this.length_limit);
    answerBar.update(answerBarControls.component);
    freeEntryKeyboard.update(this.getKeyboard());
    this.inputfield = answerBarControls.inputfield;
    this.setAnswer(this.default_answer);
  }

  this.getControl = function () {
    return (this.inputfield == null ? null : this.inputfield.child.control);
  }

  this.getRaw = function () {
    var control = this.getControl();
    return (control != null ? control.value : null);
  }

  this.getAnswer = function () {
    var raw = this.getRaw();
    return (raw == '' ? null : raw);
  }

  this.setAnswer = function (answer, postLoad) {
    var control = this.getControl();
    if (control) {
      control.value = (answer != null ? answer : '');
    } else {
      this.default_answer = answer;
    }
  }

  this.getAnswerBar = function () {
    var answerText = new InputArea({id: 'textinp', border: 3, padding: 5, child: new TextInput({textsize: 1.2, align: 'left', spacing: 0})});  
    var freeTextAnswer = make_answerbar(answerText, '*', 'answer-bar');

    return {
      component: freeTextAnswer,
      inputfield: answerText
    };
  }

  this.getKeyboard = function () {
    return kbdForDomain(this.domain, this.typeFunc());
  }

  this.typeFunc = function (no_flash) {
    flash = no_flash || false;
    var self = this;
    return function (ev, c, button) { type_(self.getControl(), c, button, !no_flash); };
  }

  this.prevalidate = function () {
    var raw = this.getRaw();
    if (raw) {
      var errmsg = this._prevalidate(raw);
      if (errmsg) {
        showError(errmsg);
        return false;
      }
    }
    return true;
  }

  this._prevalidate = function (raw) {
    return null;
  }
}

function kbdForDomain (domain, typefunc) {
  if (domain == 'full') {
    return makeKeyboard(true, typefunc);
  } else if (domain == 'alpha') {
    return makeKeyboard(false, typefunc);
  } else if (domain == 'numeric') {
    return makeNumpad(null, typefunc);
  }
}

function PasswordEntry (args) {
  args.length_limit = args.length_limit || 9;
  inherit(this, new FreeTextEntry(args));

  this.getAnswerBar = function () {
    var passwdText = new InputArea({id: 'textinp', border: 3, padding: 5, child: new TextInput({textsize: 1.3, spacing: 0, passwd: true})});
    var passwdAnswer = make_answerbar(passwdText, '5@', 'passwd-bar');

    return {
      component: passwdAnswer,
      inputfield: passwdText
    };
  }

  this.typeFunc = function () {
    //turn off keyflash
    return this.super('typeFunc')(true);
  }
}

function IntEntry (length_limit) {
  inherit(this, new FreeTextEntry({domain: 'numeric', length_limit: length_limit || 9}));

  this.getAnswer = function () {
    var val = this.super('getAnswer')();
    return (val != null ? +val : val);
  }
}

function FloatEntry () {
  inherit(this, new FreeTextEntry({}));

  this.getAnswer = function () {
    var val = this.super('getAnswer')();
    return (val != null ? +val : val);
  }

  this.getKeyboard = function () {
    return makeNumpad('.', this.typeFunc());
  }

  this._prevalidate = function (raw) {
    return (isNaN(+raw) ? "Not a valid number" : null);
  }
}

function PhoneNumberEntry () {
  inherit(this, new FreeTextEntry({length_limit: 15}));

  this.getKeyboard = function () {
    return makeNumpad('+', this.typeFunc());
  }

  this._prevalidate = function (raw) {
    return (!(/^\+?[0-9]+$/.test(raw)) ? "This does not appear to be a valid phone number" : null);
  }
}

function MultiSelectEntry (args) {
  inherit(this, new SimpleEntry());

  this.choices = args.choices;
  this.choicevals = args.choicevals;
  this.layout_override = args.layout_override;
  this.as_single = (args.meta || {}).as_single;

  this.isMulti = true;
  this.buttons = null;
  this.default_selections = null;

  this.load = function () {
    var choiceLayout = this.makeChoices();
    questionEntry.update(choiceLayout);
    this.buttons = choiceLayout.buttons;
  }

  this.makeChoices = function (style) {
    return new ChoiceSelect({choices: this.choices, choicevals: this.choicevals, selected: this.default_selections, multi: this.isMulti, action: this.selectFunc(), layout_override: this.layout_override, style: style});
  }

  this.getAnswer = function () {
    var selected = [];
    for (i = 0; i < this.buttons.length; i++) {
      if (this.buttons[i].status == 'selected') {
        selected.push(this.buttons[i].value);
      }
    }
    return selected;
  }

  //answer is null or list
  this.setAnswer = function (answer, postLoad) {
    if (this.buttons) {
      for (var i = 0; i < this.buttons.length; i++) {
        var button = this.buttons[i];
        button.setStatus(answer != null && answer.indexOf(button.value) != -1 ? 'selected': 'default');
      }
    } else {
      this.default_selections = answer;
    }
  }

  this.selectFunc = function () {
    var self = this;
    return function (ev, c, button) {
      button.toggleStatus();

      //one special value can be treated like a single-select, where if it is chosen the question
      //is answered immediately; useful for 'none of the above'-type buttons
      if (button.value == self.as_single) {
        var ans = self.getAnswer();
        if (ans.length == 1 && ans[0] == self.as_single) {
          autoAdvanceTrigger();
        }
      }
    }
  }
}

function SingleSelectEntry (args) {
  inherit(this, new MultiSelectEntry(args));

  this.isMulti = false;

  this.getAnswer = function () {
    var selected = this.super('getAnswer')();
    return selected.length > 0 ? selected[0] : null;
  }

  this.setAnswer = function (answer, postLoad) {
    this.super('setAnswer')(answer != null ? [answer] : null, postLoad);
  }

  this.selectFunc = function () {
    var togglefunc = this.super('selectFunc')();
    var self = this;
    return function (ev, c, button) {
      var oldstatus = button.status;
      togglefunc(ev, c, button);
      clearButtons(self.buttons, button);
      if (oldstatus == 'default') {
        autoAdvanceTrigger();
      }
    }
  }
}

function clearButtons (buttons, except_for) {
  for (var i = 0; i < buttons.length; i++) {
    if (buttons[i] != except_for) {
      buttons[i].resetStatus();
    }
  }
}

function DateEntry (dir, args) {
  inherit(this, new Entry());

  this.dir = dir;
  this.context = new DateWidgetContext(args);

  this.load = function () {
    this.context.refresh();
  }

  this.setAnswer = function (answer, postLoad) {
    this.context.init(answer, this.dir || postLoad);
    if (postLoad) {
      this.context.refresh();
    }
  }

  this.getAnswer = function () {
    return this.context.getDate();
  }

  this.next = function () {
    this.context.next();
  }

  this.back = function () {
    this.context.back();
  }
}

function BloodPressureEntry () {
  this.SYST_MAX = 300;
  this.SYST_MIN = 40;
  this.DIAST_MAX = 210;
  this.DIAST_MIN = 20;

  /* thresholds mean: "once the value in the field is >= this threshold value
   * we consider the field done and move on to the next. e.g., for a systolic
   * value of '20', we're probably still going to enter '220', but for a value
   * of '90', we are not going to enter '930', so we move on after the 9-0
   */
  this.getThreshold = function (min, max) {
    return Math.max(min, Math.floor(max / 10) + 1);
  }
  this.SYST_ADV_THRESH = this.getThreshold(this.SYST_MIN, this.SYST_MAX);
  this.DIAST_ADV_THRESH = this.getThreshold(this.DIAST_MIN, this.DIAST_MAX);

  inherit(this, new Entry());

  this.cur_field = null;
  this.default_answer = null;

  this.BPField = function (field, threshold, forward_trigger, backward_trigger) {
    this.threshold = threshold;
    this.forward_trigger = forward_trigger;
    this.backward_trigger = backward_trigger || function () {};
    
    inherit(this, new ShadowField(field, new IntEntry(3)));

    this.isComplete = function () {
      return this.getAnswer() >= threshold;
    }

    this.typeFunc = function () {
      var self = this;
      var type_ = this.super('typeFunc')(false);
      return function (ev, c, button) {
        if (self.isComplete() && c != BKSP) {
          self.setAnswer(null);
        } else if (self.getAnswer() == null && c == BKSP) {
          self.backward_trigger();
        }

        type_(ev, c, button);

        if (self.isComplete()) {
          self.forward_trigger();
        }
      }
    }
  }

  this.load = function () {
    this.make_fields(); 
    
    var self = this;
    this.entry = {
      syst: new this.BPField(this.fields.syst, this.SYST_ADV_THRESH, function () {
          self.activate('diast');
        }),
      diast: new this.BPField(this.fields.diast, this.DIAST_ADV_THRESH, function () {
          autoAdvanceTrigger();
        },
        function () {
          self.activate('syst');
          self.typeToEntry('syst', BKSP);
        })
    };
    
    this.activate('syst');
    answerBar.update(this.make_answerbar());
    questionEntry.update(freeEntry);
    this.setAnswer(this.default_answer);
  }
  
  this.typeToEntry = function (field, c) {
    this.entry[field].typeFunc()(null, c, null);
  }

  this.activate = function (which) {
    this.cur_field = which;
    this.entry[which].load();
    this.fields.syst.setBgColor(which == 'syst' ? HIGHLIGHT_COLOR : '#fff');
    this.fields.diast.setBgColor(which == 'diast' ? HIGHLIGHT_COLOR : '#fff');
  }
  
  this.goto_ = function (field) {
    this.activate(field);
  }
  
  this.setAnswer = function (answer, postLoad) {
    if (this.entry) {
      var match = /^([0-9]+) *\/ *([0-9]+)$/.exec(answer);
      if (!match) {
        var bp = {syst: null, diast: null};
        this.activate('syst');
      } else {
        var bp = {syst: +match[1], diast: +match[2]};
      }

      for (t in bp) {
        this.entry[t].setAnswer(bp[t]);
      }
    } else {
      this.default_answer = answer;
    }
  }

  this.getRaw = function () {
    return {
      syst: this.entry.syst.getAnswer(),
      diast: this.entry.diast.getAnswer()
    };
  }

  this.getAnswer = function () {
    return (this.isEmpty() ? null : this.fmtBp());
  }

  this.next = function () {
    var advance = false;
    if (this.isEmpty()) {
      advance = true;
    } else if (this.isFull()) {
      if (this.isInRange()) {
        advance = true;
      } else {
        showError(this.outOfRangeMsg());
        return;
      }
    }
    
    if (advance) {
      answerQuestion();
    } else {
      if (this.getRaw()[this.cur_field] == null) {
        showError('Enter a ' + (this.cur_field == 'syst' ? 'systolic' : 'diastolic') + ' blood pressure')
      } else {
        this.activate(this.cur_field == 'syst' ? 'diast' : 'syst');
      }
    }
  }
  
  this.back = function () {
    prevQuestion();
  }
  
  this.make_fields = function () {
    var self = this;
    this.fields = {
      syst: new InputArea({id: 'bp-syst', border: 3, child: new TextCaption({size: 1.6, align: 'center', color: TEXT_COLOR}), onclick: function () {self.goto_('syst');}}),
      diast: new InputArea({id: 'bp-diast', border: 3, child: new TextCaption({size: 1.6, align: 'center', color: TEXT_COLOR}), onclick: function () {self.goto_('diast');}}),
    };
  }
  
  this.make_answerbar = function () {
    var bpSpacer = new TextCaption({color: TEXT_COLOR, caption: '/', size: 1.7});
    var content = [this.fields.syst, bpSpacer, this.fields.diast];
    var widths = ['1.8@', '.5@', '1.8@'];
    return make_answerbar(content, widths, 'bp-bar');
  }
  
  this.isFull = function () {
    var bp = this.getRaw();
    return (bp.syst != null && bp.diast != null);
  }
  
  this.isEmpty = function () {
    var bp = this.getRaw();
    return (bp.syst == null && bp.diast == null);
  }
  
  this.isInRange = function () {
    var bp = this.getRaw();
    return (bp.syst <= this.SYST_MAX && bp.syst >= this.SYST_MIN && bp.diast <= this.DIAST_MAX && bp.diast >= this.DIAST_MIN);
  }
  
  this.outOfRangeMsg = function () {
    return 'Blood pressure must be between ' + this.fmtBp({syst: this.SYST_MIN, diast: this.DIAST_MIN}) + ' and ' + this.fmtBp({syst: this.SYST_MAX, diast: this.DIAST_MAX});
  }
  
  this.fmtBp = function (bp) {
    bp = bp || this.getRaw();
    return bp.syst + '/' + bp.diast;
  }
}

function UnitEntry (unit, prototype) {
  this.unit = unit;

  inherit(this, prototype);

  this.getAnswerBar = function () {
    //i think something isn't quite right with the text sizing... seems to ignore font size
    //got it looking ok for now
    var labelsz = (this.unit.length > 2 ? 1.1 : 1.3);
    var height = getTextExtent('I', labelsz)[1];
    var width = getTextExtent(this.unit, labelsz)[0];
    var labelaspect = (labelsz / 1.75 * width / height);
    var counterbalance = 2.

    var answerText = new InputArea({id: 'textinp', border: 3, padding: 5, child: new TextInput({textsize: 1.2, align: 'center', spacing: 0})});  
    var unitLabel = new TextCaption({color: TEXT_COLOR, caption: this.unit, size: labelsz, align: 'left'});
    var freeTextAnswer = make_answerbar([null, answerText, unitLabel], [counterbalance + '@', '3.5@', labelaspect + '@'], 'answer-bar');
    
    return {
      component: freeTextAnswer,
      inputfield: answerText
    };
  }
}

/* field that behaves like an <input>, but has no cursor and is otherwise not manipulable like a normal <input>
 * this is accomplished by using a hidden <input>, whose contents are then copied to a <span>
 */
function ShadowField (displayfield, prototype) {
  inherit(this, prototype);
  
  this.displayfield = displayfield;

  this.make_input = function () {
    var inputfield = document.createElement('input');
    $('body')[0].appendChild(inputfield);
    inputfield.style.visibility = 'hidden';
    if (this.length_limit) {
      inputfield.maxLength = this.length_limit;
    }
    return inputfield;
  }
  this.inputfield = this.make_input();

  this.getControl = function () {
    return this.inputfield;
  }
  
  this.load = function () {
    freeEntryKeyboard.update(this.getKeyboard());
  }
  
  this.fieldChanged = function () {
    this.displayfield.setText(this.getRaw());
  }
  
  this.setAnswer = function (answer, postLoad) {
    this.super('setAnswer')(answer, postLoad);
    this.fieldChanged();
  }

  this.typeFunc = function (no_flash) {
    var self = this;
    var type_ = this.super('typeFunc')(no_flash);
    return function (ev, c, button) {
      type_(ev, c, button);
      self.fieldChanged();
    }
  }
}

AUTOCOMPL_BLACK_ON_WHITE = true;
function AutoCompleteEntry (lookup_key, prototype, style) {
  this.CURRENT_TEXT_AS_SUGGESTION = true;

  inherit(this, prototype);

  this.lookup_key = lookup_key;
  this.style = style || 'sidebaralt';

  this.ChoiceField = function (choices, parent, selected, style, settext) {
    this.style = style;
    this.choiceStyling = function () {
      if (this.style == 'list') {
        return {forceMode: 'list', listStretch: true, margin: 20}
      } else {
        return {forceMode: 'grid', spacing: .05, margin: 5, maxText: 1.6};
      }
    }

    inherit(this, new SingleSelectEntry({choices: choices, choicevals: choices, layout_override: this.choiceStyling()}));

    this.parent = parent;
    this.settext = settext;
    this.selected = selected;
    
    this.load = function () {
      this.setAnswer(this.selected);

      var choiceLayout = this.makeChoices(AUTOCOMPL_BLACK_ON_WHITE ? {color: '#fff', textcolor: '#000', selcolor: '#fcc'} : {color: 'gr #198 #044'});
      parent.update(choiceLayout);
      this.buttons = choiceLayout.buttons;

      //hack - css annoyances
      for (var i = 0; i < this.buttons.length; i++) {
        var btn = this.buttons[i];
        btn.base_style = null;
        btn.setStatus(btn.status);
      }
    }

    this.selectFunc = function () {
      var selfunc = this.super('selectFunc')();
      var self = this;
      return function (ev, c, button) {
        if (button.status == 'selected') {
          autoAdvanceTrigger();
          return;
        }

        selfunc(ev, c, button);
        self.settext(self.getAnswer());
      }
    }
  }

  this.load = function () {
    this.suggestions = new Indirect();
    var keyboard = new Indirect();
    var answerBar = new Indirect();

    if (this.style.substring(0, 7) == 'sidebar') {
      this.top = new Layout({id: 'autocomp-split', ncols: 2, widths: ['*', '40%'], content: [
          new Layout({id: 'ac-free-entry', nrows: 2, heights: ['18%', '*'], content: [
            answerBar,
            new Layout({id: 'ac-kbd', margins: ['1.5%=', '1.5%=', 0, '2%='], content: [keyboard]})
          ]}),
          this.suggestions
        ]});
      this.MAX_SUGGESTIONS = 9;
    } else if (this.style == 'inline') {
      this.top = new Layout({id: 'autocomp-split', nrows: 3, heights: ['18%', '*', '60%'], content: [
          answerBar,
          new Layout({margins: ['5%', 0], content: [this.suggestions]}),
          new Layout({id: 'kbd', margins: ['1.5%=', '1.5%=', '3%=', '4%='], content: [keyboard]})
        ]});
      this.MAX_SUGGESTIONS = 6;
    }

    /* very similar to FreeTextEntry.load() */
    questionEntry.update(this.top);
    var answerBarControls = this.getAnswerBar();
    answerBarControls.inputfield.setMaxLen(this.length_limit);
    answerBar.update(answerBarControls.component);
    keyboard.update(this.getKeyboard());
    this.inputfield = answerBarControls.inputfield;
    this.setAnswer(this.default_answer);
    // ----
  }

  this.getAnswer = function () {
    answer = null;
    if (this.choiceControl) {
      answer = this.choiceControl.getAnswer();
    }
    if (answer == null) {
      answer = this.getTextAnswer();
    }
    return answer;
  }

  this.getTextAnswer = function () {
    return this.super('getAnswer')();
  }

  this.setAnswer = function (answer, postLoad) {
    this.super('setAnswer')(answer, postLoad);
    if (this.suggestions) {
      this.textChanged();
    }
  }

  this.getKeyboard = function () {
    return makeKeyboard(false, this.typeFunc(), {inline: null, sidebar: 'condensed', sidebaralt: 'supercondensed'}[this.style]);
  }

  this.typeFunc = function () {
    var self = this;
    var type_ = this.super('typeFunc')(false);
    return function (ev, c, button) {
      type_(ev, c, button);
      self.textChanged();
    };
  }

  //todo: should we wait until typing has stopped for a short delay before querying, to ease burden on the server?
  this.textChanged = function () {
    this.refreshChoices();
  }

  this.getSearchKey = function () {
    return this.getTextAnswer() || '';
  }

  this.refreshChoices = function () {
    var params = {
      domain: this.lookup_key,
      max: this.MAX_SUGGESTIONS,
      key: this.getSearchKey()
    }
    var self = this;
    jQuery.get(AUTOCOMPLETE_URL, params, function (data) {
        if (self.getSearchKey() != params.key) {
          console.log('results no longer valid');
        } else {
          self.updateChoices(data);
        }
      }, 'json');
  }

  this.updateChoices = function (results) {
    var current = this.getSearchKey();
    if (this.CURRENT_TEXT_AS_SUGGESTION) {
      if (results.length < this.MAX_SUGGESTIONS && current) {
        var exists = false;
        for (var i = 0; i < results.length; i++) {
          if (results[i].name == current) {
            exists = true;
            break;
          }
        }
        if (!exists) {
          results.push({name: current, p: 0.});
        }
      }
    }

    if (this.style == 'inline') {
      //sort by likelihood
      results.sort(function (a, b) { return cmp(b.p, a.p); });
    } else {
      //sort by name
      results.sort(function (a, b) { return cmp(a.name, b.name); });
    }


    var names = [];
    for (var i = 0; i < results.length; i++) {
      console.log(results[i]);
      names.push(results[i].name);
    }
    this.setChoices(names, current);
  }

  this.setChoices = function (choices, selected) {
    if (choices.length > 0) {
      var self = this;
      this.choiceControl = new this.ChoiceField(choices, this.suggestions, selected, this.style == 'inline' ? 'bar' : 'list', function (x) { self.super('setAnswer')(x); });
      this.choiceControl.load();
    } else {
      this.choiceControl = null;
      this.suggestions.update(new TextCaption({caption: 'no suggestions'}));
    }
  }
}

function IDMaskEntry (mask, prefix, prototype) {
  inherit(this, prototype);

  this.mask = mask;
  this.prefix = prefix;

  this.MaskedField = function (cells, domain) {
    inherit(this, new ShadowField(cells, new FreeTextEntry({domain: domain, length_limit: cells.length})));

    this.fieldChanged = function () {
      var str = this.getRaw();
      for (var i = 0; i < this.displayfield.length; i++) {
        //todo: don't overwrite chars that haven't changed, for increased speed?
        this.displayfield[i].setText(i < str.length ? str[i] : '');
      }
    }

    this.typeFunc = function () {
      var self = this;
      var type_ = this.super('typeFunc')(false);
      return function (ev, c, button) {
        type_(ev, c, button);
        if (self.getRaw().length == self.displayfield.length) {
          autoAdvanceTrigger();
        }
      }
    }
  }

  this.load = function () {
    questionEntry.update(freeEntry);
    var answerBarControls = this.getAnswerBar();
    answerBar.update(answerBarControls.component);
    this.inputfield = answerBarControls.inputfield;
    this.inputfield.load();
    this.setAnswer(this.default_answer);
  }

  this.setAnswer = function (answer, postLoad) { 
    if (!answer && !postLoad && this.prefix) {
      answer = this.prefix;
    }

    if (this.inputfield) {
      this.inputfield.setAnswer(answer);
    } else {
      this.default_answer = answer;
    }
  }

  this.getControl = function () {
    return (this.inputfield == null ? null : this.inputfield.getControl());
  }

  this.getAnswerBar = function () {
    var mkspacer = function (c) {
      if (c == '-') {
        c = '\u2013';
      }
      return new TextCaption({color: TEXT_COLOR, caption: c, size: 1.4});
    };

    var cells = [];
    var content = [];
    var widths = [];
    for (var i = 0; i < this.mask.length; i++) {
      if (this.mask[i] != 'x') {
        content.push(mkspacer(this.mask[i]));
        widths.push('.33@');
      } else {
        var cell = new InputArea({id: 'mask-' + i, border: 2, child: new TextCaption({size: 1.6, align: 'center', color: TEXT_COLOR})});
        cells.push(cell);
        content.push(cell);
        widths.push('.7@');
      }
    }

    var answerText = new this.MaskedField(cells, this.domain);
    var freeTextAnswer = make_answerbar(content, widths, 'answer-bar');

    return {
      component: freeTextAnswer,
      inputfield: answerText
    };
  }
}

