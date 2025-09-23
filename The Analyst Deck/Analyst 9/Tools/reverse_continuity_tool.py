
class ReverseContinuityTool:
    def __init__(self):
        self.triggers = {
            "time_gap_without_reason": self.detect_time_gap,
            "location_conflict": self.detect_location_conflict,
            "subject_swap_without_transition": self.detect_subject_swap,
            "conflicting_tense_usage": self.detect_conflicting_tense,
            "ambiguous_pronoun_reference": self.detect_ambiguous_pronoun,
            "dangling_modifier": self.detect_dangling_modifier,
            "inconsistent_verb_object": self.detect_inconsistent_verb_object,
            "dual_actor_confusion": self.detect_dual_actor_confusion,
            "missing_transitional_anchor": self.detect_missing_transitional_anchor,
            "plural_singular_conflict": self.detect_plural_singular_conflict
        }
        self.log = []

    def run_validation(self, text, documents, assets):
        flags = []
        for trigger_name, trigger_func in self.triggers.items():
            if trigger_func(text):
                flags.append(trigger_name)
                self.log.append(f"Trigger activated: {trigger_name}")

        if flags:
            if self.resolve_with_documents(documents):
                self.log.append("Continuity resolved via documents.")
                return True, self.log
            elif self.resolve_with_assets(assets):
                self.log.append("Continuity resolved via field assets.")
                return True, self.log
            else:
                self.log.append("Manual intervention required.")
                return False, self.log
        else:
            return True, ["No continuity issues found."]

    # Placeholder detection logic
    def detect_time_gap(self, text): return "hours later" in text
    def detect_location_conflict(self, text): return "different place" in text
    def detect_subject_swap(self, text): return "suddenly" in text
    def detect_conflicting_tense(self, text): return "was" in text and "is" in text
    def detect_ambiguous_pronoun(self, text): return "they" in text and "they" not in text.split()[0:10]
    def detect_dangling_modifier(self, text): return "Running down the street" in text
    def detect_inconsistent_verb_object(self, text): return "opens the books and closes the window fast" in text
    def detect_dual_actor_confusion(self, text): return "he and he" in text
    def detect_missing_transitional_anchor(self, text): return "then" not in text and "after" not in text
    def detect_plural_singular_conflict(self, text): return "agents goes" in text

    def resolve_with_documents(self, docs):
        return any("verified" in doc.lower() for doc in docs)

    def resolve_with_assets(self, assets):
        return any("confirmed" in asset.lower() for asset in assets)
