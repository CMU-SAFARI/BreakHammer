from .run_config import MEM_HIST_PREC

def get_mem_hist(hist_file):
    mem_hist = []
    def cleanup(token):
        return int(token.lstrip().strip())
    with open(hist_file, "r", encoding="utf-8") as f:
        for line in f:
            tokens = line.split(",")
            mem_hist.append((cleanup(tokens[0]), cleanup(tokens[1])))
    mem_hist = sorted(mem_hist, key=lambda x: x[0])
    for i in range(1, len(mem_hist)):
        mem_hist[i] = (mem_hist[i][0], mem_hist[i][1] + mem_hist[i-1][1]) 
    return mem_hist

def get_pN(mem_hist, N):
    _, total_reqs = mem_hist[-1]
    pN_loc = total_reqs * (N / 100)
    for bucket, running_sum in mem_hist:
        if running_sum >= pN_loc:
            return bucket + MEM_HIST_PREC - 1

def get_mean(mem_hist):
    sum_cycles = (mem_hist[0][0] + MEM_HIST_PREC - 1) * mem_hist[0][1]
    prev_count = mem_hist[0][1]
    for i in range(1, len(mem_hist)):
        cur_bucket, cur_runsum = mem_hist[i]
        cur_count = cur_runsum - prev_count
        sum_cycles += (cur_bucket + MEM_HIST_PREC - 1) * cur_count
        prev_count = cur_runsum
    return sum_cycles / mem_hist[-1][1]

def get_mem_stats(hist_file):
    mem_hist = get_mem_hist(hist_file)
    mem_stats = {
        "mean": get_mean(mem_hist),
        "P90": get_pN(mem_hist, 90),
        "P99": get_pN(mem_hist, 99)
    }
    return mem_stats