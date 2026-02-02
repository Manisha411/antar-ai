package com.journal.repository;

import com.journal.model.entity.JournalEntry;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface JournalEntryRepository extends JpaRepository<JournalEntry, UUID> {

    Page<JournalEntry> findByUserIdOrderByCreatedAtDesc(String userId, Pageable pageable);

    List<JournalEntry> findByUserIdAndCreatedAtAfterOrderByCreatedAtDesc(String userId, Instant since);

    @Query("SELECT e FROM JournalEntry e WHERE e.userId = :userId AND e.id = :id")
    Optional<JournalEntry> findByUserIdAndId(String userId, UUID id);

    @Query("SELECT e FROM JournalEntry e WHERE e.userId = :userId ORDER BY e.createdAt DESC")
    List<JournalEntry> findRecentByUserId(String userId, Pageable pageable);

    Page<JournalEntry> findByUserIdAndCreatedAtBetweenOrderByCreatedAtDesc(
        String userId, Instant from, Instant to, Pageable pageable);

    void deleteByUserId(String userId);
}
