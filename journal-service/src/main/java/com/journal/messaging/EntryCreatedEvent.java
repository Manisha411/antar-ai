package com.journal.messaging;

import java.time.Instant;
import java.util.UUID;

public class EntryCreatedEvent {

    private UUID entryId;
    private String userId;
    private String content;
    private Instant createdAt;
    private String source = "journal-service";

    public EntryCreatedEvent() {
    }

    public EntryCreatedEvent(UUID entryId, String userId, String content, Instant createdAt) {
        this.entryId = entryId;
        this.userId = userId;
        this.content = content;
        this.createdAt = createdAt;
    }

    public UUID getEntryId() {
        return entryId;
    }

    public void setEntryId(UUID entryId) {
        this.entryId = entryId;
    }

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }
}
