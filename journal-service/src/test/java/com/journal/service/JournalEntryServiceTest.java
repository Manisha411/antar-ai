package com.journal.service;

import com.journal.messaging.EntryCreatedEvent;
import com.journal.messaging.EntryEventPublisher;
import com.journal.model.dto.CreateEntryRequest;
import com.journal.model.dto.EntryResponse;
import com.journal.model.entity.JournalEntry;
import com.journal.repository.JournalEntryRepository;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class JournalEntryServiceTest {

    @Mock
    private JournalEntryRepository repository;

    @Mock
    private EntryEventPublisher eventPublisher;

    @InjectMocks
    private JournalEntryService service;

    @Test
    void create_persistsEntryAndPublishesEvent() {
        String userId = "user-1";
        CreateEntryRequest request = new CreateEntryRequest();
        request.setContent("Test content");
        JournalEntry saved = new JournalEntry();
        saved.setId(UUID.randomUUID());
        saved.setUserId(userId);
        saved.setContent("Test content");
        saved.setCreatedAt(java.time.Instant.now());
        saved.setUpdatedAt(java.time.Instant.now());
        when(repository.save(any(JournalEntry.class))).thenReturn(saved);

        EntryResponse response = service.create(userId, request);

        assertThat(response).isNotNull();
        assertThat(response.getContent()).isEqualTo("Test content");
        assertThat(response.getUserId()).isEqualTo(userId);
        ArgumentCaptor<EntryCreatedEvent> eventCaptor = ArgumentCaptor.forClass(EntryCreatedEvent.class);
        verify(eventPublisher).publishEntryCreated(eventCaptor.capture());
        assertThat(eventCaptor.getValue().getUserId()).isEqualTo(userId);
        assertThat(eventCaptor.getValue().getContent()).isEqualTo("Test content");
    }

    @Test
    void getById_throwsWhenNotFound() {
        String userId = "user-1";
        UUID id = UUID.randomUUID();
        when(repository.findByUserIdAndId(userId, id)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.getById(userId, id))
            .isInstanceOf(EntryNotFoundException.class);
    }
}
