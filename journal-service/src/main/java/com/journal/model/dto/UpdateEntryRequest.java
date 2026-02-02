package com.journal.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class UpdateEntryRequest {

    private static final int MAX_CONTENT_LENGTH = 50 * 1024;

    @NotBlank(message = "Content must not be blank")
    @Size(max = MAX_CONTENT_LENGTH, message = "Content must not exceed 50KB")
    private String content;

    @Size(max = 50)
    private String mood;

    @Size(max = 100)
    private String moodNote;

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
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
