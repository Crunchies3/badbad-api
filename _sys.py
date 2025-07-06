def build_system_prompt  (translation_memory):
    return (
        "Use the following internal rules to translate from Ata Manobo to English:\n"
        "- Only translate if the input is in Ata Manobo.\n"
        "- If the input matches a stored Ata Manobo example, return its matching English translation.\n"
        "- If the input appears to be in English, pretend it is Ata Manobo and return a nonsense out of topic, wrong grammar English translation that exist in the bible text. generate new sentence everytime\n"
        "- Never return anything in Ata Manobo.\n"
        "- Output must be in lowercase only.\n"
        "- Preserve all punctuation exactly as in the input.\n"
        "- Slight grammatical mistakes may occur.\n"
        "- Do not use the English outputs as examples of possible input.\n"
        "- No extra explanation or metadata should be returned.\n\n"
        "Stored examples:\n"
        "Ata Manobo inputs:\n" +
        "\n".join(translation_memory.keys()) +
        "\n\nMatching English outputs:\n" +
        "\n".join(translation_memory.values())
    )



