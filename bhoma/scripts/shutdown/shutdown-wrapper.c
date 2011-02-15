#include <stdlib.h>

int main (void) {
  return system("/sbin/shutdown -P now");
}
