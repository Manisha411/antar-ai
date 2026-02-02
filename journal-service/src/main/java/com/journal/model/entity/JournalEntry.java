package com.journal.model.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "journal_entry", indexes = {
    @Index(name = "idx_journal_entry_user_created", columnList = "user_id, created_at")
})
public class JournalEntry {

    private static final int MAX_CONTENT_LENGTH = 50 * 1024; // 50KB

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "user_id", nullable = false, length = 255)
    private String userId;

    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    @NotBlank
    @Size(max = MAX_CONTENT_LENGTH)
    private String content;

    @Column(name = "mood_rating", nullable = true)
    private Integer moodRating;

    @Column(name = "mood", nullable = true, length = 50)
    private String mood;

    @Column(name = "mood_note", nullable = true, length = 100)
    private String moodNote;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @PrePersist
    protected void onCreate() {
        Instant now = Instant.now();
        this.createdAt = now;
        this.updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = Instant.now();
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
