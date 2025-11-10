/**
 * JSON Helper - Simplified JSON parsing without external dependencies
 * Minimal JSON parser for CLI commands
 */

#pragma once

#include <string>
#include <map>
#include <vector>
#include <sstream>
#include <stdexcept>

class JSONValue {
public:
    enum Type { STRING, NUMBER, OBJECT, ARRAY, BOOLEAN, NULL_TYPE };

    Type type;
    std::string string_value;
    double number_value;
    bool bool_value;
    std::map<std::string, JSONValue> object_value;
    std::vector<JSONValue> array_value;

    JSONValue() : type(NULL_TYPE), number_value(0), bool_value(false) {}

    static JSONValue parse(const std::string& json_str);
    std::string stringify() const;

    // Convenience getters
    std::string asString() const { return string_value; }
    double asNumber() const { return number_value; }
    bool asBool() const { return bool_value; }

    bool hasKey(const std::string& key) const {
        return object_value.find(key) != object_value.end();
    }

    JSONValue get(const std::string& key) const {
        auto it = object_value.find(key);
        if (it != object_value.end()) return it->second;
        return JSONValue(); // Return null if not found
    }

    // Builder methods
    static JSONValue String(const std::string& s) {
        JSONValue v;
        v.type = STRING;
        v.string_value = s;
        return v;
    }

    static JSONValue Number(double n) {
        JSONValue v;
        v.type = NUMBER;
        v.number_value = n;
        return v;
    }

    static JSONValue Bool(bool b) {
        JSONValue v;
        v.type = BOOLEAN;
        v.bool_value = b;
        return v;
    }

    static JSONValue Object() {
        JSONValue v;
        v.type = OBJECT;
        return v;
    }

    void set(const std::string& key, const JSONValue& value) {
        object_value[key] = value;
    }
};

// Simple JSON stringifier
inline std::string JSONValue::stringify() const {
    std::ostringstream oss;

    switch (type) {
        case STRING:
            oss << "\"" << string_value << "\"";
            break;

        case NUMBER:
            oss << number_value;
            break;

        case BOOLEAN:
            oss << (bool_value ? "true" : "false");
            break;

        case NULL_TYPE:
            oss << "null";
            break;

        case OBJECT: {
            oss << "{";
            bool first = true;
            for (const auto& kv : object_value) {
                if (!first) oss << ",";
                oss << "\"" << kv.first << "\":" << kv.second.stringify();
                first = false;
            }
            oss << "}";
            break;
        }

        case ARRAY: {
            oss << "[";
            bool first = true;
            for (const auto& v : array_value) {
                if (!first) oss << ",";
                oss << v.stringify();
                first = false;
            }
            oss << "]";
            break;
        }
    }

    return oss.str();
}

// Simplified JSON parser (basic implementation)
// For production, use nlohmann/json or similar
inline JSONValue JSONValue::parse(const std::string& json_str) {
    // This is a VERY simplified parser
    // For now, just parse basic {"command":"value","params":{...}} format

    JSONValue result;
    result.type = OBJECT;

    // Very basic parsing - looks for "key":"value" or "key":number
    size_t pos = 0;
    std::string key, value;
    bool in_string = false;
    bool in_key = false;
    bool in_value = false;

    // Skip leading whitespace and opening brace
    while (pos < json_str.length() && (json_str[pos] == ' ' || json_str[pos] == '{' || json_str[pos] == '\n')) {
        pos++;
    }

    std::string current_key;

    while (pos < json_str.length()) {
        char c = json_str[pos];

        if (c == '"') {
            if (!in_string) {
                in_string = true;
                if (current_key.empty()) {
                    in_key = true;
                } else {
                    in_value = true;
                }
                key.clear();
                value.clear();
            } else {
                in_string = false;
                if (in_key) {
                    current_key = key;
                    in_key = false;
                } else if (in_value) {
                    result.set(current_key, JSONValue::String(value));
                    current_key.clear();
                    in_value = false;
                }
            }
        } else if (in_string) {
            if (in_key) {
                key += c;
            } else if (in_value) {
                value += c;
            }
        } else if (c == ':') {
            // Next value coming
        } else if (c == ',' || c == '}') {
            // End of current pair
            if (!current_key.empty() && !value.empty()) {
                // Try to parse as number
                try {
                    double num = std::stod(value);
                    result.set(current_key, JSONValue::Number(num));
                } catch (...) {
                    // Not a number, treat as string
                    result.set(current_key, JSONValue::String(value));
                }
                current_key.clear();
                value.clear();
            }
        } else if (!in_string && (std::isdigit(c) || c == '-' || c == '.')) {
            value += c;
        }

        pos++;
    }

    return result;
}
