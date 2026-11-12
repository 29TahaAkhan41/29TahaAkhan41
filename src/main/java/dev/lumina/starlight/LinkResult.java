package dev.lumina.starlight;

/** Outcome of trying to aim one node's beam at another. */
public enum LinkResult {
    LINKED,
    ALREADY_LINKED,
    SAME_BLOCK,
    CANNOT_EMIT,
    NOT_A_NODE,
    TOO_FAR,
    NO_LINE_OF_SIGHT,
    NO_FREE_OUTPUT,
    WOULD_LOOP;

    public String translationKey() {
        return "message.lumina.link." + name().toLowerCase(java.util.Locale.ROOT);
    }
}
