# Core Concepts

## Architecture Overview

LLM Response → Parser → ParserEvents → Toolbox → Tool Execution

## Key Components

| Component       | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| **Parsers**     | Convert raw LLM output to structured events with streaming support         |
| **Formatters**  | Generate model-specific prompts with tool documentation                    |
| **Toolbox**     | Central registry for tools with schema validation and type conversion      |
| **Events**      | Streaming-friendly units representing text chunks or tool invocations      |

## Type Conversion System

The Toolbox automatically converts arguments using these mappings:

| Input Value | Type      | Result          |
|-------------|-----------|-----------------|
| "42"        | integer   | 42 (int)        |
| "3.14"      | number    | 3.14 (float)    |
| "true"      | boolean   | True (bool)     |
| "hello"     | string    | "hello" (str)   |
