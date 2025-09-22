# Core Concepts

## Architecture Overview

## Key Components

| Component       | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| **Parsers**     | Convert raw LLM output to structured events with streaming support         |
| **Formatters**  | Generate model-specific prompts with tool documentation                    |
| **Toolbox**     | Central registry for tools with schema validation and type conversion      |
| **Events**      | Streaming-friendly units representing text chunks or tool invocations      |

Tools themselves are simply functions. They can either by async or normal python functions.

## Type Conversion System

The Toolbox automatically converts arguments using these mappings. Supported literal types are `int`, `float`, `bool`, and `string`:

| Input Value | Literal Type | Result          |
|-------------|--------------|-----------------|
| "42"        | int          | 42 (int)        |
| "3.14"      | float        | 3.14 (float)    |
| "true"      | bool         | True (bool)     |
| "hello"     | string       | "hello" (str)   |

## Patterns

### Write only(No Feedback)
LLM Response → Parser → ParserEvents → Toolbox → Tool Execution

### Read-write(Feedback)
LLM Response → Parser → ParserEvents → Toolbox → Tool Execution → Insert Tool Response → Call LLM
