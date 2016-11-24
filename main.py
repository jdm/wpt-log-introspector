import itertools
import json
import sys

def rr_trace_directory(output):
    for data in reversed(output):
        if "action" in data and data["action"] == "process_output" and \
           "Saving execution" in data["data"]:
            return data["data"][data["data"].index('`')+1:-2]
    raise "no rr trace found for process %s" % output[0]["process"]


def process_structured_wpt_output(lines):
    unfiltered_data = map(lambda line: json.loads(line), lines)

    per_thread_output = {}
    for data in unfiltered_data:
        if data["thread"] not in per_thread_output:
            per_thread_output[data["thread"]] = []
        per_thread_output[data["thread"]] += [data]

    per_test_output = []
    for name, thread_results in per_thread_output.iteritems():
        if name == "MainThread":
            continue

        tests = []
        test = []
        state = 0
        for data in thread_results:
            if "action" in data and data["action"] == "log":
                continue

            if state == 0:
                assert data["action"] == "test_start"
                state = 1
                test += [data]
            elif state == 1:
                if not "action" in data or data["action"] in ["process_output", "crash", "test_status"]:
                    test += [data]
                else:
                    if data["action"] != "test_end":
                        print data, data["action"]
                    assert data["action"] == "test_end"
                    test += [data]
                    tests += [test]
                    test = []
                    state = 0

        per_test_output += tests

    unexpected_tests = filter(lambda test: "expected" in test[-1], per_test_output)
    return unexpected_tests
    

def usage():
    print '%s log [test [-v]]' % sys.argv[0]
    return 1


def process_single_test(result, verbose):
    print '%s (%s, expected %s)' % (
        result[0]["test"], result[-1]["status"], result[-1]["expected"])
    print '  rr replay %s' % rr_trace_directory(result)
    print ''
    if verbose:
        for data in result:
            print data
    else:
        print '%s' % result[0]["thread"]
        command = None
        start = result[0]["time"]
        for time, data in itertools.groupby(result, lambda d: d["time"]):
            print '%.2fs' % ((time - start) / 1000.0)
            for data in data:
                if "command" in data and command != data["command"]:
                    command = data["command"]
                    start = time
                    print '%.2fs' % ((time - start) / 1000.0)
                    print '%s' % command

                if "action" in data and data["action"] == "process_output":
                    print data["data"]

def process_single_matching_test(testname, verbose):
    matching = filter(lambda test: testname in test[0]["test"], unexpected_results)
    if not matching:
        print 'no matching test found with unexpected results'
        return 1
    elif len(matching) > 1:
        print 'multiple matching tests found with unexpected results; use a more specific test name.'
        return 1
    else:
        process_single_test(matching[0], verbose)
        return 0


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        sys.exit(usage())
    verbose = False
    if len(sys.argv) == 4:
        if sys.argv[3] != '-v':
            sys.exit(usage())
        else:
            verbose = True
    fname = sys.argv[1]
    with open(fname) as f:
        unexpected_results = process_structured_wpt_output(f.readlines())

        if len(sys.argv) > 2:
            sys.exit(process_single_matching_test(sys.argv[2], verbose))
        else:
            for result in unexpected_results:
                print '%s (%s, expected %s)' % (
                    result[0]["test"], result[-1]["status"], result[-1]["expected"])
                print '  rr replay %s' % rr_trace_directory(result)
