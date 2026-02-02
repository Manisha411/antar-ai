package com.journal.model.dto;

import java.time.Instant;
import java.util.UUID;

public class EntryResponse {

    private UUID id;
    private String userId;
    private String content;
    private Integer moodRating;
    private String mood;
    private String moodNote;
    private Instant createdAt;
    private Instant updatedAt;

    public EntryResponse() {
    }

    public EntryResponse(UUID id, String userId, String content, Integer moodRating, String mood, String moodNote,
                        Instant createdAt, Instant updatedAt) {
        this.id = id;
        this.userId = userId;
        this.content = content;
        this.moodRating = moodRating;
        this.mood = mood;
        this.moodNote = moodNote;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
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

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(Instant updatedAt) {
        this.updatedAt = updatedAt;
    }

    public Integer getMoodRating() {
        return moodRating;
    }

    public void setMoodRating(Integer moodRating) {
        this.moodRating = moodRating;
    }

    public String getMood() {
        return mood;
    }

    public void setMood(String mood) {
        this.mood = mood;
    }

    public String getMoodNote() {
        return moodNote;
    }

    public void setMoodNote(String moodNote) {
        this.moodNote = moodNote;
    }
}
