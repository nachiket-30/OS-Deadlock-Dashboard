
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="OS Deadlock Dashboard",
    page_icon="💻",
    layout="wide"
)

st.title("OS Deadlock Analysis and Resource Allocation Dashboard")
st.caption("OS IA Assignment Activity 2")

# -------------------- SESSION STATE --------------------

if "system" not in st.session_state:
    st.session_state.system = None


def safe_sequence(allocation, maximum, available):
    n = len(allocation)
    m = len(available)

    need = [
        [maximum[i][j] - allocation[i][j] for j in range(m)]
        for i in range(n)
    ]

    work = available.copy()
    finish = [False] * n
    sequence = []
    steps = []

    while True:
        found = False

        for i in range(n):
            if not finish[i] and all(
                need[i][j] <= work[j] for j in range(m)
            ):
                before = work.copy()
                work = [
                    work[j] + allocation[i][j] for j in range(m)
                ]
                finish[i] = True
                sequence.append(f"P{i}")
                steps.append({
                    "Process": f"P{i}",
                    "Need": str(need[i]),
                    "Work Before": str(before),
                    "Work After": str(work)
                })
                found = True

        if not found:
            break

    return all(finish), sequence, steps, need


def detect_deadlock(allocation, requests, available):
    n = len(allocation)
    m = len(available)

    work = available.copy()
    finish = [
        all(value == 0 for value in allocation[i])
        for i in range(n)
    ]

    progress = True
    while progress:
        progress = False

        for i in range(n):
            if not finish[i] and all(
                requests[i][j] <= work[j] for j in range(m)
            ):
                work = [
                    work[j] + allocation[i][j] for j in range(m)
                ]
                finish[i] = True
                progress = True

    return [f"P{i}" for i in range(n) if not finish[i]]


# -------------------- SIDEBAR --------------------

page = st.sidebar.radio(
    "Select Module",
    [
        "System Configuration",
        "Banker's Algorithm",
        "Resource Request",
        "Deadlock Detection",
        "Deadlock Prevention",
        "Boundary Testing"
    ]
)

# -------------------- SYSTEM CONFIGURATION --------------------

if page == "System Configuration":
    st.header("System Configuration")
    st.write("Enter your own processes, resource types, and resource matrices.")

    n = st.number_input(
        "Number of processes",
        min_value=1, max_value=10, value=5, step=1,
        key="config_n"
    )

    m = st.number_input(
        "Number of resource types",
        min_value=1, max_value=5, value=3, step=1,
        key="config_m"
    )

    resource_names = [f"R{j}" for j in range(int(m))]
    process_names = [f"P{i}" for i in range(int(n))]

    st.subheader("Allocation Matrix")
    default_allocation = pd.DataFrame(
        0, index=process_names, columns=resource_names
    )
    allocation_df = st.data_editor(
        default_allocation,
        key=f"allocation_{n}_{m}",
        num_rows="fixed",
        use_container_width=True
    )

    st.subheader("Maximum Matrix")
    default_maximum = pd.DataFrame(
        1, index=process_names, columns=resource_names
    )
    maximum_df = st.data_editor(
        default_maximum,
        key=f"maximum_{n}_{m}",
        num_rows="fixed",
        use_container_width=True
    )

    st.subheader("Available Resources")
    available_values = []
    cols = st.columns(int(m))
    for j in range(int(m)):
        with cols[j]:
            available_values.append(
                st.number_input(
                    f"Available {resource_names[j]}",
                    min_value=0, value=1, step=1,
                    key=f"available_{n}_{m}_{j}"
                )
            )

    if st.button("Save System Configuration", type="primary"):
        allocation = allocation_df.values.tolist()
        maximum = maximum_df.values.tolist()
        available = [int(x) for x in available_values]

        valid = True

        for i in range(int(n)):
            for j in range(int(m)):
                a = allocation[i][j]
                mx = maximum[i][j]

                if pd.isna(a) or pd.isna(mx):
                    st.error("Matrices cannot contain empty values.")
                    valid = False
                    break

                if int(a) != a or int(mx) != mx or a < 0 or mx < 0:
                    st.error("Allocation and Maximum must be non-negative integers.")
                    valid = False
                    break

                if a > mx:
                    st.error(
                        f"Invalid input: Allocation of P{i} for "
                        f"{resource_names[j]} exceeds Maximum."
                    )
                    valid = False
                    break

        if valid:
            allocation = [
                [int(x) for x in row] for row in allocation
            ]
            maximum = [
                [int(x) for x in row] for row in maximum
            ]

            st.session_state.system = {
                "allocation": allocation,
                "maximum": maximum,
                "available": available,
                "processes": int(n),
                "resources": int(m),
                "resource_names": resource_names,
                "process_names": process_names
            }
            st.success("System configuration saved successfully.")

    if st.session_state.system:
        st.success("A system configuration is available for the other modules.")
        st.write("Processes:", st.session_state.system["processes"])
        st.write("Resource types:", st.session_state.system["resources"])
        st.write("Available:", st.session_state.system["available"])

# -------------------- BANKER'S ALGORITHM --------------------

elif page == "Banker's Algorithm":
    st.header("Banker's Algorithm - Safety Check")
    system = st.session_state.system

    if not system:
        st.warning("First configure and save the system in System Configuration.")
    else:
        allocation = system["allocation"]
        maximum = system["maximum"]
        available = system["available"]
        names = system["resource_names"]
        processes = system["process_names"]

        need = [
            [maximum[i][j] - allocation[i][j]
             for j in range(len(available))]
            for i in range(len(allocation))
        ]

        st.subheader("Allocation")
        st.dataframe(pd.DataFrame(allocation, index=processes, columns=names))

        st.subheader("Maximum")
        st.dataframe(pd.DataFrame(maximum, index=processes, columns=names))

        st.subheader("Need = Maximum - Allocation")
        st.dataframe(pd.DataFrame(need, index=processes, columns=names))

        st.write("Available:", available)

        safe, sequence, steps, need = safe_sequence(
            allocation, maximum, available
        )

        if safe:
            st.success("SAFE STATE: All processes can finish.")
            st.subheader("Safe Sequence")
            st.write(" → ".join(sequence))
        else:
            st.error("UNSAFE STATE: No complete safe sequence exists.")

        if steps:
            st.subheader("Work Vector Updates")
            st.dataframe(pd.DataFrame(steps), hide_index=True)

# -------------------- RESOURCE REQUEST --------------------

elif page == "Resource Request":
    st.header("Resource Request Simulator")
    system = st.session_state.system

    if not system:
        st.warning("First configure and save the system.")
    else:
        allocation = system["allocation"]
        maximum = system["maximum"]
        available = system["available"]
        names = system["resource_names"]
        processes = system["processes"]
        m = system["resources"]

        process = st.selectbox(
            "Select requesting process",
            range(processes),
            format_func=lambda x: f"P{x}"
        )

        request = []
        cols = st.columns(m)
        for j in range(m):
            with cols[j]:
                request.append(
                    st.number_input(
                        f"Request {names[j]}",
                        min_value=0, value=0, step=1,
                        key=f"request_{process}_{j}"
                    )
                )
        request = [int(x) for x in request]

        need = [
            [maximum[i][j] - allocation[i][j] for j in range(m)]
            for i in range(processes)
        ]

        if st.button("Check and Process Request", type="primary"):
            if any(request[j] > need[process][j] for j in range(m)):
                st.error("INVALID REQUEST: Request exceeds remaining Need.")
                st.info("Original allocation remains unchanged.")

            elif any(request[j] > available[j] for j in range(m)):
                st.warning("WAITING / DEFERRED: Available resources are insufficient.")
                st.info("Original allocation remains unchanged.")

            else:
                temp_allocation = [row.copy() for row in allocation]
                temp_available = available.copy()

                for j in range(m):
                    temp_allocation[process][j] += request[j]
                    temp_available[j] -= request[j]

                safe, sequence, steps, _ = safe_sequence(
                    temp_allocation, maximum, temp_available
                )

                if safe:
                    st.success("REQUEST GRANTED: The resulting state is safe.")
                    st.write("Safe sequence:", " → ".join(sequence))
                    st.subheader("Simulated Allocation after grant")
                    st.dataframe(pd.DataFrame(
                        temp_allocation,
                        index=system["process_names"],
                        columns=names
                    ))
                    st.write("Simulated Available:", temp_available)
                    st.caption(
                        "This is a simulation. The saved original configuration "
                        "has not been permanently changed."
                    )
                else:
                    st.error("REQUEST DENIED: The resulting state is unsafe.")
                    st.info("Temporary allocation rolled back; original state unchanged.")

# -------------------- DEADLOCK DETECTION --------------------

elif page == "Deadlock Detection":
    st.header("Deadlock Detection and Recovery")
    st.write(
        "Enter a separate system's Allocation, outstanding Request, and Available "
        "vectors to test for deadlock."
    )

    n = st.number_input(
        "Number of processes for detection",
        min_value=1, max_value=8, value=2, step=1,
        key="detect_n"
    )
    m = st.number_input(
        "Number of resource types for detection",
        min_value=1, max_value=5, value=2, step=1,
        key="detect_m"
    )

    processes = [f"P{i}" for i in range(int(n))]
    resources = [f"R{j}" for j in range(int(m))]

    allocation_df = st.data_editor(
        pd.DataFrame(0, index=processes, columns=resources),
        key=f"detect_alloc_{n}_{m}",
        num_rows="fixed",
        use_container_width=True
    )

    request_df = st.data_editor(
        pd.DataFrame(0, index=processes, columns=resources),
        key=f"detect_req_{n}_{m}",
        num_rows="fixed",
        use_container_width=True
    )

    available = []
    cols = st.columns(int(m))
    for j in range(int(m)):
        with cols[j]:
            available.append(
                st.number_input(
                    f"Detection Available {resources[j]}",
                    min_value=0, value=0, step=1,
                    key=f"detect_avail_{n}_{m}_{j}"
                )
            )

    if st.button("Run Deadlock Detection", type="primary"):
        alloc = allocation_df.values.tolist()
        requests = request_df.values.tolist()
        available = [int(x) for x in available]

        valid = True
        for matrix in [alloc, requests]:
            for row in matrix:
                for value in row:
                    if pd.isna(value) or int(value) != value or value < 0:
                        valid = False

        if not valid:
            st.error("Enter only non-negative integer values.")
        else:
            alloc = [[int(x) for x in row] for row in alloc]
            requests = [[int(x) for x in row] for row in requests]

            deadlocked = detect_deadlock(alloc, requests, available)

            st.session_state.detection_result = {
                "allocation": alloc,
                "requests": requests,
                "available": available,
                "deadlocked": deadlocked,
                "n": int(n),
                "m": int(m),
                "resources": resources
            }

            if deadlocked:
                st.error("Potentially deadlocked processes: " + ", ".join(deadlocked))
                st.write(
                    "Interpretation depends on the resource model and the "
                    "correctness of the outstanding request matrix."
                )
            else:
                st.success("No deadlocked processes detected for this input.")

    result = st.session_state.get("detection_result")
    if result:
        st.divider()
        st.subheader("Recovery Simulation")

        if result["deadlocked"]:
            victim = st.selectbox(
                "Choose a process to terminate",
                [int(p[1:]) for p in result["deadlocked"]],
                format_func=lambda x: f"P{x}"
            )

            if st.button("Terminate Process and Release Resources"):
                alloc = [row.copy() for row in result["allocation"]]
                requests = [row.copy() for row in result["requests"]]
                avail = result["available"].copy()

                for j in range(result["m"]):
                    avail[j] += alloc[victim][j]
                    alloc[victim][j] = 0
                    requests[victim][j] = 0

                remaining = detect_deadlock(alloc, requests, avail)

                st.write(f"Terminated P{victim} and released its resources.")
                st.write("Available after recovery:", avail)

                if remaining:
                    st.error("Remaining deadlocked processes: " + ", ".join(remaining))
                else:
                    st.success("No deadlocked processes remain in the recovery simulation.")
        else:
            st.info("No detected deadlock to recover from. Enter a deadlocked scenario first.")

# -------------------- DEADLOCK PREVENTION --------------------

elif page == "Deadlock Prevention":
    st.header("Deadlock Prevention by Resource Ordering")
    st.write("Set a fixed resource order and test a process's next request.")

    resource_count = st.number_input(
        "Number of resources",
        min_value=2, max_value=5, value=3, step=1,
        key="prevention_m"
    )
    resources = [f"R{i}" for i in range(int(resource_count))]

    held = st.multiselect(
        "Resources currently held",
        resources
    )
    requested = st.selectbox(
        "Next resource requested",
        resources
    )

    if st.button("Check Ordering Policy", type="primary"):
        order = {resource: i for i, resource in enumerate(resources)}

        if requested in held:
            st.warning("This resource is already held.")
        elif held and order[requested] < max(order[r] for r in held):
            st.error("REQUEST REJECTED: This request violates the fixed resource order.")
            st.write("The policy requires resources to be acquired in ascending order.")
        else:
            st.success("REQUEST ALLOWED: This request follows the resource order.")

    st.subheader("Policy comparison")
    st.write(
        "**Original policy:** Processes may request resources in any order, "
        "which can permit circular wait."
    )
    st.write(
        "**Prevention policy:** Every process must request resources in a fixed order. "
        "If every process obeys the rule, circular wait is prevented."
    )
    st.warning(
        "Trade-off: a fixed ordering can reduce flexibility and concurrency."
    )

# -------------------- BOUNDARY TESTING --------------------

elif page == "Boundary Testing":
    st.header("Boundary and Invalid Input Testing")
    system = st.session_state.system

    st.write("Use the saved configuration to check boundary conditions.")

    if system:
        allocation = system["allocation"]
        maximum = system["maximum"]
        available = system["available"]
        need = [
            [maximum[i][j] - allocation[i][j]
             for j in range(system["resources"])]
            for i in range(system["processes"])
        ]

        zero_available = all(value == 0 for value in available)
        zero_need_processes = [
            f"P{i}" for i, row in enumerate(need)
            if all(value == 0 for value in row)
        ]

        st.write("Available vector:", available)
        if zero_available:
            st.warning("Boundary case: all Available resources are zero.")
        else:
            st.success("Available contains at least one resource.")

        if zero_need_processes:
            st.success(
                "Processes with zero remaining Need: "
                + ", ".join(zero_need_processes)
            )
        else:
            st.info("No process currently has zero remaining Need.")

        invalid_process = st.number_input(
            "Example process ID to validate",
            min_value=-1, max_value=system["processes"],
            value=system["processes"], step=1
        )

        if invalid_process < 0 or invalid_process >= system["processes"]:
            st.error("Invalid process ID.")
        else:
            st.success("Process ID is within the valid range.")

        st.caption(
            "Negative requests and Allocation exceeding Maximum are rejected "
            "in the Resource Request and System Configuration modules."
        )
    else:
        st.warning("Save a system in System Configuration to run these checks.")

st.divider()
st.caption("OS IA Assignment Activity 2 | User-configurable dashboard")
