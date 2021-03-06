# Tutorial: Test Framework (Under Development)

## Using the test framework

**Not yet implemented. Notes only.**

- Using the TestRunner
- Writing a custom test
- Using the TestController
  - Multiple test iterations

## Build an image and check it boots

**Not yet implemented. Notes only.**

- Build Raspberry Pi image using Yocto
- Flash image to SD Card using SD Wire
- Insert SD Card into target
- Power on target
- Check target boots & measure boot time

## Monitor target performance

**Not yet implemented. Notes only.**

- Download application source via git (E.g. calculate prime numbers)

```C
include <stdio.h>
include <stdlib.h>

int main(int argc, char **argv)
{
  int n, i=3, c, count;

  if (argc < 2) {
    printf("Must give number of primes to calculate\n");
    exit(1);
  }
  n = atoi(argv[1]);

  if (n >= 1) {
    printf("First %d prime numbers are:\n",n);
    printf("2\n");
  }

  for (count = 2; count <= n;) {
    for (c = 2; c <= i - 1; c++) {
      if (i%c == 0)
        break;
    }
    if (c == i) {
      printf("%d\n", i);
      count++;
    }
    i++;
  }

  return 0;
}
```

- Build the application (maybe build natively on target for simplicity)
- Copy application/source to target via SCP
- Measure how long application takes for different inputs

```python
n_primes = 5000
cmd =f'{ N_PRIMES={nprimes} ; /usr/bin/time -f "$N_PRIMES, %e" ./calculate_primes.o $N_PRIMES; } 2>&1 1>/dev/null'
```

```shell
{ N_PRIMES=5000 ; /usr/bin/time -f "$N_PRIMES, %e" ./calculate_primes.o $N_PRIMES; } 2>&1 1>/dev/null

primes_found=5000, seconds_taken=0.27
```

- Copy file to host
- Plot data in graph
- Send graph via email

___

<< Previous: [Tutorial Set: Hardware Control](./2-tutorial-hardware-control.md) |
Next: [Tutorial Set: Reporting](./4-tutorial-reporting.md) >>
