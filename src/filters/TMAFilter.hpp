#pragma once

#include "./Common.hpp"

#include <array>

template <std::size_t N>
class TMAFilter
{
public:
    static constexpr std::size_t BufferSize = next_power_of_two(N);
    static constexpr std::size_t BufferMask = BufferSize - 1;
    static constexpr std::size_t BufferShift = size_as_bitshift(BufferSize);

private:
    std::int_fast16_t index_ = 0;
    std::array<SampleType, BufferSize> buffer_;
    SampleAccumType accum_;

public:
    TMAFilter() : buffer_(), accum_(0) {}

    SampleType operator()(SampleType sample)
    {
        accum_ += sample - buffer_[index_];
        buffer_[index_] = sample;
        index_ = (index_ + 1) & TMAFilter::BufferMask;
        return clamped_cast(accum_ >> TMAFilter::BufferShift);
    }
};
