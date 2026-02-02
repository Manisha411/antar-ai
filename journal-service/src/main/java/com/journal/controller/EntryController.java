package com.journal.controller;

import com.journal.model.dto.CreateEntryRequest;
import com.journal.model.dto.EntryResponse;
import com.journal.model.dto.StreakResponse;
import com.journal.model.dto.UpdateEntryRequest;
import com.journal.service.EntryNotFoundException;
import com.journal.service.JournalEntryService;

import jakarta.validation.Valid;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/entries")
public class EntryController {

    private final JournalEntryService service;

    public EntryController(JournalEntryService service) {
        this.service = service;
    }

    @PostMapping
    public ResponseEntity<EntryResponse> create(
            @AuthenticationPrincipal UserDetails user,
            @Valid @RequestBody CreateEntryRequest request) {
        String userId = user.getUsername();
        EntryResponse created = service.create(userId, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @GetMapping
    public ResponseEntity<Page<EntryResponse>> list(
            @AuthenticationPrincipal UserDetails user,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant from,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant to) {
        String userId = user.getUsername();
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        Page<EntryResponse> result;
        if (from != null && to != null) {
            result = service.listByUserAndDateRange(userId, from, to, pageable);
        } else {
            result = service.listByUser(userId, pageable);
        }
        return ResponseEntity.ok(result);
    }

    @GetMapping("/streak")
    public ResponseEntity<StreakResponse> streak(@AuthenticationPrincipal UserDetails user) {
        String userId = user.getUsername();
        StreakResponse response = service.getStreak(userId);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/recent")
    public ResponseEntity<List<EntryResponse>> recent(
            @AuthenticationPrincipal UserDetails user,
            @RequestParam(defaultValue = "10") int limit) {
        String userId = user.getUsername();
        List<EntryResponse> list = service.getRecentByUser(userId, Math.min(limit, 100));
        return ResponseEntity.ok(list);
    }

    @GetMapping("/{id}")
    public ResponseEntity<EntryResponse> getById(
            @AuthenticationPrincipal UserDetails user,
            @PathVariable UUID id) {
        String userId = user.getUsername();
        EntryResponse entry = service.getById(userId, id);
        return ResponseEntity.ok(entry);
    }

    @PutMapping("/{id}")
    public ResponseEntity<EntryResponse> update(
            @AuthenticationPrincipal UserDetails user,
            @PathVariable UUID id,
            @Valid @RequestBody UpdateEntryRequest request) {
        String userId = user.getUsername();
        EntryResponse updated = service.update(userId, id, request);
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(
            @AuthenticationPrincipal UserDetails user,
            @PathVariable UUID id) {
        String userId = user.getUsername();
        service.delete(userId, id);
        return ResponseEntity.noContent().build();
    }

    /** Delete all journal entries for the authenticated user. */
    @DeleteMapping
    public ResponseEntity<Void> deleteAll(@AuthenticationPrincipal UserDetails user) {
        String userId = user.getUsername();
        service.deleteAllByUser(userId);
        return ResponseEntity.noContent().build();
    }
}
