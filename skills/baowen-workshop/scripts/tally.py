#!/usr/bin/env python3
"""统计一组头条内容流量数字（文章阅读/视频播放/微头条赞）。

用法：
    python3 tally.py "76,11,939,5,47,8,..."
    python3 tally.py --label 文章阅读 "1,47,19,6,8,149,939,5,151,4,11,7,4,2,33,12,18,3,11,93"

输出：条数、合计、均值、中位数、区间分布（占比%）。
"""
import sys
import statistics


def main():
    label = "流量"
    if len(sys.argv) >= 4 and sys.argv[1] == "--label":
        label = sys.argv[2]
        raw = sys.argv[3]
    else:
        raw = sys.argv[1]

    nums = [float(x) for x in raw.replace("，", ",").split(",") if x.strip()]
    if not nums:
        print("无有效数字")
        sys.exit(1)

    n = len(nums)
    total = sum(nums)
    mean = total / n
    med = statistics.median(nums)
    mx = max(nums)
    mn = min(nums)

    bands = [(0, 10, "<=10"), (10, 50, "11-50"), (50, 200, "51-200"), (200, 10**12, ">200")]
    dist = []
    for lo, hi, name in bands:
        c = sum(1 for v in nums if lo < v <= hi or (lo == 0 and v <= hi))
        pct = round(100.0 * c / n, 1)
        dist.append(f"  {name:>7s}: {c:>3d} 条, 占比 {pct} 个百分点")

    print(f"== {label} ==")
    print(f"条数: {n}  合计: {total:.0f}")
    print(f"均值: {mean:.1f}  中位数: {med:.1f}  最高: {mx:.0f}  最低: {mn:.0f}")
    print("区间分布:")
    print("\n".join(dist))


if __name__ == "__main__":
    main()
