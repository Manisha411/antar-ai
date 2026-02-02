package com.journal.service;

import java.util.UUID;

public class EntryNotFoundException extends RuntimeException {

    public EntryNotFoundException(UUID id) {
        super("Entry not found: " + id);
    }
}
