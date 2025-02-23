#pragma once

#include <algorithm>
#include <cstdint>

using SampleType = std::int16_t;
using SampleAccumType = std::int_fast32_t;
using SampleAccumType = std::int_fast32_t;

constexpr std::size_t next_power_of_two(std::size_t n)
{
    return n == 0 ? 1 : 2 << (sizeof(n) * 8 - __builtin_clz(n - 1));
}

constexpr std::size_t size_as_bitshift(std::size_t n)
{
    return sizeof(n) * 8 - __builtin_clz(n - 1);
}

inline SampleType clamped_cast(SampleAccumType x)
{
    /**/ if (__builtin_expect(x <= -0x7fff, 0))
        return -0x7fff;
    else if (__builtin_expect(x >= +0x7fff, 0))
        return +0x7fff;
    else
        return SampleType(x);
}
