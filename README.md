# load_testing_data_viewer
Process data from various load testing tools (tsung, artillery.io, locust) and view results as charts and tables

## [TSUNG](http://tsung.erlang-projects.org/) 

### Tsung data format

http://tsung.erlang-projects.org/user_manual/faq.html#what-format-stats

Every 10 sec dump data at `tsung.log` file:

```
# stats: dump at 1746469501
stats: {load,"tsung_controller@f6f41ca75a60"} 1 0.16015625 0.0 0.21875 0.16015625 0.19921875 2
stats: {cpu,"tsung_controller@f6f41ca75a60"} 1 0.6793817003241087 0.0 0.6793817003241087 0.5304874243275292 0.5858234467778842 2
stats: {freemem,"tsung_controller@f6f41ca75a60"} 1 123662.24609375 0.0 123668.2578125 123646.546875 123657.40234375 2
stats: request 595 89.66055126050429 32.136904181826715 442.028 48.044 93.5522566666666 300
stats: connect 11 115.67118181818182 5.531918750112954 348.6 102.827 127.93686666666666 15
stats: page 146 359.9922808219178 50.83031810943222 812.473 309.92 379.6534861111111 72
stats: users 26 26
stats: users_count 11 26
stats: finish_users_count 0 0
stats: connected 11 26
stats: nomatch 1190 1790
stats: size_sent 925090 1394924
stats: size_rcv 877293 1319453
stats: 200 595 895
stats: error_connect_closed 0 1
stats: tr_rand_name 163 0.26987730061349685 0.16868054437057947 1.776 0.16 0.2646521739130435 92
stats: tr_get_host_name 11 0.07172727272727274 0.021032835407744154 0.197 0.061 0.0902 15
stats: tr_read_file 11 0.1447272727272727 0.0059404760918925605 0.309 0.127 0.1908 15
stats: tr_cb_balance 149 77.66687919463088 14.249574393697284 211.546 66.098 74.88512987012986 77
stats: tr_cb_login 149 106.13193288590601 9.39066762617517 235.81 93.45 107.17295945945946 74
stats: tr_cb_liveness 151 68.08050331125828 48.720415074362826 456.855 48.651 87.52762337662338 77
stats: tr_set_var 11 0.4305454545454545 0.06175223755440126 1.062 0.384 0.4992 15
```

#### Block header with timestamp, every 10 sec

`# stats: dump at timestamp`

Get `timestamp` from it.

#### transaction record format

`stats: name, 10sec_count, 10sec_mean, 10sec_stddev, max, min, mean, count`

First 3 records for name `tr_cb_win`:
```
stats: tr_login 8 113.1775 10.454288988257401 132.339 102.556 0 0
stats: tr_login 64 109.26742187499998 6.675797620426833 132.339 97.829 113.1775 8
stats: tr_login 146 110.63634246575347 11.06102719315203 188.704 94.706 109.70187499999999 72
```
* `10sec_count` - requests into this 10 sec interval.
* `10sec_mean` - mean request time into this 10 sec interval.
* `10sec_stddev` - standard deviation request time into this 10 sec interval.
* `max` - max request time since test start.
* `min` - min request time since test start.
* `mean` - mean request time since test start.
* `count` - requests BEFORE this 10 sec interval, next block 'count' is equal `10sec_count` + `count` for this interval. 

Table **Transactions Statistics** with headers:

| Header | value |
|----|----|
| Name | `name` |
| highest 10sec mean | max(`10sec_mean`) |
| lowest  10sec mean | min(`10sec_mean`) |
| Highest Rate | max(`10sec_count`) / 10 |
| Mean Rate | (last(`count`) + last(`10sec_count`)) / total_time |
| Mean | last(`mean`) |
| Count | (last(`count`) + last(`10sec_count`)) | 

Charts:

* **Mean transaction and page duration** - for each transaction and `page` chart {x: test duration in second, y: `10sec_mean`}
* **Transaction and page rate** - for each transaction and `page` chart {x: test duration in second, y: `10sec_cout` / 10}

#### Main Statistics

`stats: name, 10sec_count, 10sec_mean, 10sec_stddev, max, min, mean, count`

Names: `connect`, `page`, `request`. 

Table **Main Statistics** with the same headers as for transactions.

Charts:
 
* **Main request and connection duration** - for `connect` and `request` {x: test duration in second, y: `10sec_mean`}
* **Requests and tcp/ip connection rate** - for `connect` and `request` {x: test duration in second, y: `10sec_cout` / 10}

#### Network Throughput

`stats: name 10sec_delta total`

For `size_sent` and `size_rcv`.

Table **Network Throughput** with headers:

| Header | value |
|----|----|
| Name | `name` |
| Highest Rate | `max(10sec_delta) * 8 / 10` Mbits/sec |
| Total | `last(total)` KB/MB/GB |

Charts:

* **Network Throughput** - for `size_sent` and `size_rcv` {x: test duration in second, y: `10sec_delta` / 10 in Kbit/sec}

#### Simultaneous Users

`stats: name 10sec_delta total`

For `connected`, `finish_users_count`, `users`, `users_count`.

Table **Counters Statistics** with headers:

| Header | value |
|----|----|
| Name | `name` |
| Max | `max(total)` |

Charts:

* **User arrival/departure rate** - for `user_count` and `finish_users_count` {x: test duration in second, y: `10sec_delta` / 10}
* **Simultaneous Users** - for `users` and `connected` {x: test duration in second, y: `total`}

#### Matching responses

`stats: name 10sec_delta total`

For `name` in `match`, `nomatch`, `match_loop` etc, with **match** substring, not started with `tr_`

Table **Matching responses** with headers:

| Header | value |
|----|----|
| Name | `name` |
| Highest Rate | `max(10sec_delta) / 10` "/sec" |
| Mean Rate | `last(total) / test duration` "/sec" |
| Total number | `last(total)` |

Charts:

* **Matching responses** - for all names {x: test duration in second, y: `10sec_delta` / 10}

#### Server OS monitoring

Note: I have no example with distributed load test record.

`stats: {name, "tsung_controller_id"} 10sec_count, 10sec_mean, 10sec_stddev, max, min, mean, count`

For name is `load`, `cpu` or `freemem`.

Table **Server monitoring** with headers:

| Header | value |
|----|----|
| Name | `name` |
| highest 10sec mean | `max(10sec_mean)` |
| lowest 10sec mean | `min(10sec_mean)` |

Charts:

* **CPU% mean** - for `cpu` {x: test duration in second, y: `10sec_mean`}
* **Free memory mean** - for `freemem` {x: test duration in second, y: `10sec_mean`}
* **CPU Load** - for `load` {x: test duration in second, y: `10sec_mean`}

### HTTP return code Status (rate)

`stats: name 10sec_delta total`

Where `name` is http status code (200, 201, 500, etc).

Table **HTTP return code** with headers:

| Header | value |
|----|----|
| Name | `name` |
| Highest Rate | `max(10sec_delta) / 10` "/sec" |
| Mean Rate | `last(total) / test duration` "/sec" |
| Total number | `last(total)` |

Charts:

* **HTTP Code Respose rate** - for all names {x: test duration in second, y: `10sec_delta` / 10}

### Errors

`stats: name 10sec_delta total`

Where `name` starts with `error_`.

Table **HTTP return code** with headers:

| Header | value |
|----|----|
| Name | `name` |
| Highest Rate | `max(10sec_delta) / 10` "/sec" |
| Total number | `last(total)` |

Charts:

* **Errors (rate)** - for all names {x: test duration in second, y: `10sec_delta` / 10}
