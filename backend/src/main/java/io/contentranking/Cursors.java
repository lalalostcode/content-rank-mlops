package io.contentranking;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

final class Cursors {
    private Cursors() {}

    static String encode(String scope, Object position) {
        String payload = scope + "\n" + position;
        return Base64.getUrlEncoder().withoutPadding().encodeToString(payload.getBytes(StandardCharsets.UTF_8));
    }

    static String[] decode(String cursor) {
        try {
            if (cursor.isBlank() || cursor.length() > 512) throw new IllegalArgumentException();
            String payload = new String(Base64.getUrlDecoder().decode(cursor), StandardCharsets.UTF_8);
            String[] parts = payload.split("\n", -1);
            if (parts.length != 2 || parts[0].isBlank() || parts[1].isBlank()) {
                throw new IllegalArgumentException();
            }
            return parts;
        } catch (IllegalArgumentException ignored) {
            throw ApiException.invalid("Invalid cursor.");
        }
    }
}
