package com.journal.messaging;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class EntryEventPublisher {

    private final KafkaTemplate<String, EntryCreatedEvent> kafkaTemplate;

    @Value("${journal.topic:journal.entry.created}")
    private String topic;

    public EntryEventPublisher(KafkaTemplate<String, EntryCreatedEvent> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void publishEntryCreated(EntryCreatedEvent event) {
        kafkaTemplate.send(topic, event.getEntryId().toString(), event);
    }
}
