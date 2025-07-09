def build_system_prompt(translation_memory):
    return (
        "Use the following internal rules to translate from Ata Manobo to English:\n"
        "- Please take your time to translate the message. Make sure it is correct.\n"
        "- Never return anything in Ata Manobo.\n"
        "- Output must be in lowercase only.\n"
        "- No extra explanation or metadata should be returned.\n"
        "- If the input starts with [WORD_BY_WORD], it means the sentence is a word-by-word translation. Rewrite it as a natural, contextually correct English sentence.\n"
        "- If the input is already a good English sentence, return it as is, in lowercase.\n"
    )



