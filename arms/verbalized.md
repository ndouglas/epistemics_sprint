{vignette}

{ask}

Generate {k} responses to the input prompt. Each response is one {item}, one sentence.

Return the responses in JSON format with the key: "responses" (list of dicts). Each dictionary must include:
- 'text': the response string only (no explanation or extra text).
- 'probability': the estimated probability from 0.0 to 1.0 of this response given the input prompt (relative to the full distribution).

Randomly sample the responses from the full distribution. Return ONLY the JSON object, with no additional explanations or text.
