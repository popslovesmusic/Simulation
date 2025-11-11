/**
 * DASE CLI - Headless JSON Interface
 * Main entry point for command-line JSON-based engine control
 */

#include <iostream>
#include <string>

#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif

#include "json.hpp"
#include "command_router.h"

using json = nlohmann::json;

int main(int argc, char** argv) {
    try {
        // Handle --describe flag for engine introspection
        if (argc == 3 && std::string(argv[1]) == "--describe") {
            std::string engine_name = argv[2];
            CommandRouter router;
            json describe_cmd = {
                {"command", "describe_engine"},
                {"params", {{"engine_name", engine_name}}}
            };
            json response = router.execute(describe_cmd);
            std::cout << response.dump(2) << std::endl;
            return response["status"] == "success" ? 0 : 1;
        }

        // Set binary mode for stdin/stdout on Windows (prevents line-ending issues)
        #ifdef _WIN32
        _setmode(_fileno(stdin), _O_BINARY);
        _setmode(_fileno(stdout), _O_BINARY);
        #endif

        // Disable cout buffering for immediate output
        std::cout.setf(std::ios::unitbuf);

        // Create command router
        CommandRouter router;

        // Read JSON commands from stdin line-by-line
        std::string line;
        while (std::getline(std::cin, line)) {
            // Skip empty lines
            if (line.empty() || line == "\n" || line == "\r\n") {
                continue;
            }

            try {
                // Parse JSON command
                json command = json::parse(line);

                // Execute command
                json response = router.execute(command);

                // Output JSON response
                std::cout << response.dump() << std::endl;

            } catch (const json::parse_error& e) {
                // JSON parsing error
                json error_response = {
                    {"status", "error"},
                    {"error", std::string("JSON parse error: ") + e.what()},
                    {"error_code", "PARSE_ERROR"}
                };
                std::cout << error_response.dump() << std::endl;

            } catch (const std::exception& e) {
                // Other error
                json error_response = {
                    {"status", "error"},
                    {"error", e.what()},
                    {"error_code", "INTERNAL_ERROR"}
                };
                std::cout << error_response.dump() << std::endl;
            }
        }

        return 0;

    } catch (const std::exception& e) {
        // Fatal error (to stderr, not stdout)
        std::cerr << "FATAL: " << e.what() << std::endl;
        return 1;
    }
}
