- [x] delete topic ticks
- [x] check number of products: 381
- [x] parition topic
    - docker exec -it real_crypto-redpanda-1 rpk topic create ticks \
        --partitions 50 \
        --replicas 1
- [ ] tumble window py
    - what do I want?

product_id      — which coin
window_start    — start of the 1-min window
window_end      — end of the 1-min window
avg_spread      — average bid-ask spread over the window
avg_price       — average price over the window
price_open      — first price in the window
price_close     — last price in the window  
total_volume    — sum of volume ticks seen
ind_volatility  — where close price sits in the day range

docker exec real_crypto-redpanda-1 rpk topic create ticks --partitions=50 --replicas=1 
docker exec real_crypto-jobmanager-1 flink run -py /opt/flink/src/consume_ticks_tumble.py -pyfs /opt/flink/src