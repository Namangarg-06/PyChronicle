import math
import time


def calculate_primes(limit: int) -> list[int]:
    primes: list[int] = []
    for candidate in range(2, limit):
        is_prime = True
        for divisor in range(2, int(math.sqrt(candidate)) + 1):
            if candidate % divisor == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
    return primes


def format_primes(primes: list[int]) -> str:
    return ", ".join(str(value) for value in primes)


def main() -> None:
    limit = 50
    start_time = time.time()
    prime_list = calculate_primes(limit)
    result = format_primes(prime_list)
    duration = time.time() - start_time
    print(f"Found {len(prime_list)} primes under {limit} in {duration:.4f} seconds.")
    print(result)


if __name__ == "__main__":
    main()
