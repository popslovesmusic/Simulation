#include <iostream>
#include "src/json_helper.h"

int main() {
    std::cout << "Testing JSON helper..." << std::endl;

    JSONValue test = JSONValue::String("hello");
    std::cout << test.stringify() << std::endl;

    return 0;
}
