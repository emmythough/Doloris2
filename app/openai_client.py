    temperature: float = 1.0
):
    """
    Legacy wrapper for backward compatibility.
    Returns the raw OpenAI message object (not async).
    """
    try:
        # Prepare arguments
        api_args = {
            "model": model,
            "messages": messages,
            "tools": tools
        }
        
        if temperature != 1.0 and not model.startswith("o1") and not model.startswith("o3"):
            api_args["temperature"] = temperature

        response = client.chat.completions.create(**api_args)
        return response.choices[0].message
    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        raise e
