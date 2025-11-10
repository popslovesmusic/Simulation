#include "../src/cpp/igsoa_complex_engine_2d.h"
#include "../src/cpp/igsoa_state_init_2d.h"
#include <cmath>
#include <iostream>

int main() {
    using namespace dase::igsoa;

    const size_t N_x = 32;
    const size_t N_y = 32;

    IGSOAComplexConfig config;
    config.num_nodes = N_x * N_y;
    config.R_c_default = 4.0;
    config.kappa = 1.0;
    config.gamma = 0.1;
    config.dt = 0.01;
    config.normalize_psi = false;

    IGSOAComplexEngine2D engine(config, N_x, N_y);

    // Initialize centered circular Gaussian packet
    IGSOAStateInit2D::initCircularGaussian(
        engine,
        /*amplitude=*/1.0,
        static_cast<double>(N_x) / 2.0,
        static_cast<double>(N_y) / 2.0,
        /*sigma=*/4.0,
        /*baseline_phi=*/0.0,
        /*mode=*/"overwrite",
        /*beta=*/1.0
    );

    double x0 = 0.0;
    double y0 = 0.0;
    IGSOAStateInit2D::computeCenterOfMass(engine, x0, y0);

    engine.runMission(8);

    double x1 = 0.0;
    double y1 = 0.0;
    IGSOAStateInit2D::computeCenterOfMass(engine, x1, y1);

    const double drift = std::sqrt((x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0));
    if (drift > 0.5) {
        std::cerr << "Center-of-mass drift too large: " << drift << std::endl;
        return 1;
    }

    std::cout << "Initial center: (" << x0 << ", " << y0 << ")\n";
    std::cout << "Final center: (" << x1 << ", " << y1 << ")\n";
    std::cout << "Drift: " << drift << std::endl;
    return 0;
}
