### Pub/Sub

**Pub/Sub** combines the **horizontal scalability** of distributed streaming platforms such as **Apache Kafka** and **Pulsar** with the **enterprise messaging features** of traditional middleware like **Apache ActiveMQ** and **RabbitMQ**.
Examples of these features include **dead-letter queues**, **message filtering**, and **exactly-once delivery**.

Another key capability that Pub/Sub adopts from messaging middleware is **per-message parallelism**, rather than **partition-based messaging**.
Pub/Sub *leases individual messages* to subscriber clients and tracks whether each message is successfully processed.

By contrast, partition-based systems restrict horizontal scaling — subscribers must process messages in sequence within each partition, which **limits concurrency** to the number of partitions available. With **per-message processing**, Pub/Sub allows:

- **Maximum parallelism** of subscriber applications
- **Publisher–subscriber independence**
- **Simplified scaling** without manual partition management


#### **Lingo Overview**

- **Horizontal scalability** — Pub/Sub can handle increasing workloads simply by adding more publishers or subscribers. This allows it to process **millions of messages per second** without performance degradation. There’s no need to manually partition topics or assign consumers — Pub/Sub scales automatically.

- **Dead-letter queues (DLQs)** — Messages that repeatedly fail to be processed are redirected to a **special topic** (the DLQ).  
  This ensures no data is lost and makes it easier to inspect, debug, or retry failed messages later.

- **Message filtering** — Subscribers can define filters to receive **only messages matching specific attributes** (e.g., messages for a certain region or type).  
  This reduces unnecessary processing and improves efficiency.

- **Exactly-once delivery** — Pub/Sub ensures that each message is **delivered and processed only once**, even in the event of retries or transient errors.
