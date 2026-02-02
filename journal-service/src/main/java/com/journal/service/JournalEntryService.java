package com.journal.service;

import com.journal.messaging.EntryCreatedEvent;
import com.journal.messaging.EntryEventPublisher;
import com.journal.model.dto.CreateEntryRequest;
import com.journal.model.dto.EntryResponse;
import com.journal.model.dto.StreakResponse;
import com.journal.model.dto.UpdateEntryRequest;
import com.journal.model.entity.JournalEntry;
import com.journal.repository.JournalEntryRepository;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class JournalEntryService {

    private static final Logger log = LoggerFactory.getLogger(JournalEntryService.class);

    private final JournalEntryRepository repository;
    private final EntryEventPublisher eventPublisher;

    public JournalEntryService(JournalEntryRepository repository, EntryEventPublisher eventPublisher) {
        this.repository = repository;
        this.eventPublisher = eventPublisher;
    }

    @Transactional
    public EntryResponse create(String userId, CreateEntryRequest request) {
        JournalEntry entry = new JournalEntry();
        entry.setUserId(userId);
        entry.setContent(request.getContent().trim());
        if (request.getMood() != null && !request.getMood().isBlank()) {
            entry.setMood(request.getMood().trim());
        }
        if (request.getMoodNote() != null && !request.getMoodNote().isBlank()) {
            entry.setMoodNote(request.getMoodNote().trim());
        }
        entry = repository.save(entry);

        EntryCreatedEvent event = new EntryCreatedEvent(
            entry.getId(),
            entry.getUserId(),
            entry.getContent(),
            entry.getCreatedAt()
        );
        try {
            eventPublisher.publishEntryCreated(event);
        } catch (Exception e) {
            log.warn("Failed to publish entry.created event (Kafka may be down). Entry saved. {}", e.getMessage());
        }

        return toResponse(entry);
    }

    public Page<EntryResponse> listByUser(String userId, Pageable pageable) {
        return repository.findByUserIdOrderByCreatedAtDesc(userId, pageable)
            .map(this::toResponse);
    }

    public Page<EntryResponse> listByUserAndDateRange(String userId, java.time.Instant from,
                                                       java.time.Instant to, Pageable pageable) {
        return repository.findByUserIdAndCreatedAtBetweenOrderByCreatedAtDesc(userId, from, to, pageable)
            .map(this::toResponse);
    }

    public List<EntryResponse> getRecentByUser(String userId, int limit) {
        return repository.findRecentByUserId(userId, Pageable.ofSize(limit))
            .stream()
            .map(this::toResponse)
            .collect(Collectors.toList());
    }

    public EntryResponse getById(String userId, UUID id) {
        JournalEntry entry = repository.findByUserIdAndId(userId, id)
            .orElseThrow(() -> new EntryNotFoundException(id));
        return toResponse(entry);
    }

    @Transactional
    public EntryResponse update(String userId, UUID id, UpdateEntryRequest request) {
        JournalEntry entry = repository.findByUserIdAndId(userId, id)
            .orElseThrow(() -> new EntryNotFoundException(id));
        entry.setContent(request.getContent().trim());
        if (request.getMood() != null && !request.getMood().isBlank()) {
            entry.setMood(request.getMood().trim());
        } else if (request.getMood() != null && request.getMood().isBlank()) {
            entry.setMood(null);
        }
        if (request.getMoodNote() != null && !request.getMoodNote().isBlank()) {
            entry.setMoodNote(request.getMoodNote().trim());
        } else if (request.getMoodNote() != null && request.getMoodNote().isBlank()) {
            entry.setMoodNote(null);
        }
        entry = repository.save(entry);
        return toResponse(entry);
    }

    @Transactional
    public void delete(String userId, UUID id) {
        JournalEntry entry = repository.findByUserIdAndId(userId, id)
            .orElseThrow(() -> new EntryNotFoundException(id));
        repository.delete(entry);
    }

    @Transactional
    public void deleteAllByUser(String userId) {
        repository.deleteByUserId(userId);
    }

    public StreakResponse getStreak(String userId) {
        Instant now = Instant.now();
        Instant fourHundredDaysAgo = now.minus(400, ChronoUnit.DAYS);
        List<JournalEntry> entries = repository.findByUserIdAndCreatedAtAfterOrderByCreatedAtDesc(userId, fourHundredDaysAgo);
        Set<LocalDate> distinctDates = entries.stream()
            .map(e -> e.getCreatedAt().atOffset(ZoneOffset.UTC).toLocalDate())
            .collect(Collectors.toSet());
        LocalDate today = LocalDate.now(ZoneOffset.UTC);
        int streak = 0;
        for (LocalDate expected = today; distinctDates.contains(expected); expected = expected.minusDays(1)) {
            streak++;
        }
        Instant weekAgo = now.minus(7, ChronoUnit.DAYS);
        long entriesThisWeek = entries.stream().filter(e -> !e.getCreatedAt().isBefore(weekAgo)).count();
        return new StreakResponse(streak, (int) entriesThisWeek);
    }

    private EntryResponse toResponse(JournalEntry entry) {
        return new EntryResponse(
            entry.getId(),
            entry.getUserId(),
            entry.getContent(),
            entry.getMoodRating(),
            entry.getMood(),
            entry.getMoodNote(),
            entry.getCreatedAt(),
            entry.getUpdatedAt()
        );
    }
}
