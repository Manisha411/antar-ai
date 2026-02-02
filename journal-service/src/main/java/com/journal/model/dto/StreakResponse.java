package com.journal.model.dto;

public class StreakResponse {

    private int streak;
    private int entriesThisWeek;

    public StreakResponse() {
    }

    public StreakResponse(int streak, int entriesThisWeek) {
        this.streak = streak;
        this.entriesThisWeek = entriesThisWeek;
    }

    public int getStreak() {
        return streak;
    }

    public void setStreak(int streak) {
        this.streak = streak;
    }

    public int getEntriesThisWeek() {
        return entriesThisWeek;
    }

    public void setEntriesThisWeek(int entriesThisWeek) {
        this.entriesThisWeek = entriesThisWeek;
    }
}
