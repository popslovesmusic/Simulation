#!/usr/bin/env julia
"""
Julia Static Code Analysis for IGSOA-SIM
Automatically discovers Julia files and runs static analysis tools
"""

using Pkg
using Dates

# Configuration
const PROJECT_ROOT = dirname(dirname(dirname(@__FILE__)))
const ANALYSIS_OUTPUT_DIR = joinpath(PROJECT_ROOT, "build", "analysis_reports", "julia")
const TIMESTAMP = Dates.format(now(), "yyyymmdd_HHMMSS")

# Directories to analyze
const SOURCE_DIRS = [
    "src/julia",
    "benchmarks/julia",
]

# ANSI color codes
const COLORS = Dict(
    :header => "\033[95m\033[1m",
    :okgreen => "\033[92m",
    :warning => "\033[93m",
    :fail => "\033[91m",
    :info => "\033[96m",
    :endc => "\033[0m",
    :bold => "\033[1m"
)

function print_header(text::String)
    println()
    println("$(COLORS[:header])$("=" ^ 80)$(COLORS[:endc])")
    println("$(COLORS[:header])$(lpad(text, 40 + length(text) ÷ 2))$(COLORS[:endc])")
    println("$(COLORS[:header])$("=" ^ 80)$(COLORS[:endc])")
    println()
end

function print_success(text::String)
    println("$(COLORS[:okgreen])[OK] $text$(COLORS[:endc])")
end

function print_warning(text::String)
    println("$(COLORS[:warning])[WARN] $text$(COLORS[:endc])")
end

function print_error(text::String)
    println("$(COLORS[:fail])[ERROR] $text$(COLORS[:endc])")
end

function print_info(text::String)
    println("$(COLORS[:info])[INFO] $text$(COLORS[:endc])")
end

function find_julia_files()::Vector{String}
    """Find all Julia source files in the project"""
    print_header("Discovering Julia Source Files")

    jl_files = String[]

    for source_dir in SOURCE_DIRS
        dir_path = joinpath(PROJECT_ROOT, source_dir)
        if !isdir(dir_path)
            print_warning("Directory not found: $source_dir")
            continue
        end

        print_info("Scanning: $source_dir")

        for (root, dirs, files) in walkdir(dir_path)
            for file in files
                if endswith(file, ".jl")
                    push!(jl_files, joinpath(root, file))
                end
            end
        end
    end

    sort!(jl_files)
    print_success("Found $(length(jl_files)) Julia files")

    return jl_files
end

function check_package_installed(pkg_name::String)::Bool
    """Check if a Julia package is installed"""
    try
        deps = Pkg.dependencies()
        for (uuid, dep) in deps
            if dep.name == pkg_name && dep.is_direct_dep
                print_success("$pkg_name found: $(dep.version)")
                return true
            end
        end
    catch
    end

    print_error("$pkg_name not found!")
    print_info("Install with: using Pkg; Pkg.add(\"$pkg_name\")")
    return false
end

function run_lint_jl(jl_files::Vector{String}, mode::String)
    """Run Lint.jl on Julia files"""
    print_header("Running Lint.jl ($(uppercase(mode)) mode)")

    # Create output directory
    mkpath(ANALYSIS_OUTPUT_DIR)

    # Load Lint.jl
    try
        @eval using Lint
    catch e
        print_error("Failed to load Lint.jl: $e")
        return (1, 0)
    end

    # Output file
    report_file = joinpath(ANALYSIS_OUTPUT_DIR, "lint_report_$TIMESTAMP.txt")

    total_issues = 0

    open(report_file, "w") do f
        for file_path in jl_files
            rel_path = relpath(file_path, PROJECT_ROOT)

            try
                # Run linting on file
                result = Lint.lintfile(file_path)

                if !isempty(result)
                    for msg in result
                        total_issues += 1
                        line = "$(rel_path):$(msg.line): $(msg.code): $(msg.message)\n"
                        write(f, line)
                    end
                end
            catch e
                write(f, "Error linting $rel_path: $e\n")
            end
        end

        if total_issues == 0
            write(f, "No issues found!\n")
        end
    end

    print_success("Lint.jl analysis complete!")
    print_info("Found $total_issues issues")
    print_info("Report: $(relpath(report_file, PROJECT_ROOT))")

    return (0, total_issues)
end

function run_jet_jl(jl_files::Vector{String}, mode::String)
    """Run JET.jl type analysis"""
    print_header("Running JET.jl Type Analysis ($(uppercase(mode)) mode)")

    # Output file
    report_file = joinpath(ANALYSIS_OUTPUT_DIR, "jet_report_$TIMESTAMP.txt")

    # Load JET.jl
    try
        @eval using JET
    catch e
        print_error("Failed to load JET.jl: $e")
        print_info("JET.jl requires Julia 1.7+")
        return (1, 0)
    end

    total_issues = 0

    open(report_file, "w") do f
        write(f, "JET.jl Type Inference Analysis\n")
        write(f, "================================\n\n")

        for file_path in jl_files
            rel_path = relpath(file_path, PROJECT_ROOT)

            try
                # Analyze file
                write(f, "Analyzing: $rel_path\n")

                # Run JET report on the file
                result = JET.report_file(file_path)

                # Count issues from result
                if !isempty(JET.get_reports(result))
                    reports = JET.get_reports(result)
                    total_issues += length(reports)

                    for report in reports
                        write(f, "  Issue: $report\n")
                    end
                else
                    write(f, "  No issues found\n")
                end
                write(f, "\n")
            catch e
                write(f, "Error analyzing $rel_path: $e\n\n")
            end
        end

        write(f, "\n================================\n")
        write(f, "Total type issues found: $total_issues\n")
    end

    print_success("JET.jl analysis complete!")
    print_info("Found $total_issues type issues")
    print_info("Report: $(relpath(report_file, PROJECT_ROOT))")

    return (0, total_issues)
end

function print_summary(lint_issues::Int, jet_issues::Int)
    """Print analysis summary"""
    print_header("Julia Analysis Summary")

    total_issues = lint_issues + jet_issues

    if total_issues == 0
        print_success("No issues found!")
        return
    end

    print_info("Total issues found: $total_issues")
    println()
    println("$(COLORS[:bold])By Tool:$(COLORS[:endc])")
    println("  Lint.jl (linting):        $(lpad(lint_issues, 5))")
    println("  JET.jl (type analysis):   $(lpad(jet_issues, 5))")
end

function parse_args()
    """Parse command line arguments"""
    args = Dict{Symbol, Any}(
        :mode => "normal",
        :dir => nothing,
        :file => nothing,
        :skip_lint => false,
        :skip_jet => false
    )

    i = 1
    while i <= length(ARGS)
        arg = ARGS[i]

        if arg == "--mode" && i < length(ARGS)
            i += 1
            args[:mode] = ARGS[i]
        elseif arg == "--dir" && i < length(ARGS)
            i += 1
            args[:dir] = ARGS[i]
        elseif arg == "--file" && i < length(ARGS)
            i += 1
            args[:file] = ARGS[i]
        elseif arg == "--skip-lint"
            args[:skip_lint] = true
        elseif arg == "--skip-jet"
            args[:skip_jet] = true
        elseif arg == "--help"
            println("""
            Julia Static Code Analysis for IGSOA-SIM

            Usage: julia run_static_analysis_julia.jl [options]

            Options:
              --mode MODE       Analysis mode: fast, normal, full (default: normal)
              --dir DIR         Analyze only files in specific directory
              --file FILE       Analyze only specific file
              --skip-lint       Skip Lint.jl
              --skip-jet        Skip JET.jl
              --help            Show this help message

            Examples:
              julia run_static_analysis_julia.jl
              julia run_static_analysis_julia.jl --mode fast
              julia run_static_analysis_julia.jl --dir src/julia
            """)
            exit(0)
        end

        i += 1
    end

    return args
end

function main()
    """Main execution flow"""
    args = parse_args()

    print_header("IGSOA-SIM Julia Static Code Analysis")
    print_info("Project root: $PROJECT_ROOT")
    print_info("Timestamp: $TIMESTAMP")
    print_info("Mode: $(uppercase(args[:mode]))")

    # Step 1: Find Julia files
    jl_files = find_julia_files()

    if isempty(jl_files)
        print_error("No Julia files found to analyze!")
        return 1
    end

    # Filter by directory or file if specified
    if args[:dir] !== nothing
        filter_dir = joinpath(PROJECT_ROOT, args[:dir])
        jl_files = filter(f -> startswith(f, filter_dir), jl_files)
        print_info("Filtered to directory: $(args[:dir]) ($(length(jl_files)) files)")
    end

    if args[:file] !== nothing
        filter_file = joinpath(PROJECT_ROOT, args[:file])
        jl_files = filter(f -> f == filter_file, jl_files)
        print_info("Filtered to file: $(args[:file])")
    end

    if isempty(jl_files)
        print_error("No files match the filter!")
        return 1
    end

    println()

    # Step 2: Check tools availability
    tools_ok = true

    if !args[:skip_lint]
        if !check_package_installed("Lint")
            tools_ok = false
            args[:skip_lint] = true
        end
    end

    if !args[:skip_jet]
        if !check_package_installed("JET")
            tools_ok = false
            args[:skip_jet] = true
        end
    end

    if !tools_ok
        print_warning("Some packages are missing. Install them and re-run.")
        print_info("Quick install: using Pkg; Pkg.add([\"Lint\", \"JET\"])")
    end

    println()

    # Step 3: Run analyses
    lint_issues = 0
    jet_issues = 0

    if !args[:skip_lint]
        _, lint_issues = run_lint_jl(jl_files, args[:mode])
        println()
    end

    if !args[:skip_jet]
        _, jet_issues = run_jet_jl(jl_files, args[:mode])
        println()
    end

    # Step 4: Display summary
    print_summary(lint_issues, jet_issues)

    println()
    print_success("Julia static analysis complete!")

    return 0
end

# Run main
try
    exit(main())
catch e
    print_error("Unexpected error: $e")
    Base.showerror(stderr, e, catch_backtrace())
    exit(1)
end
