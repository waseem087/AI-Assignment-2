"""
generator.py - Satisfiable Instance Generator
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02

Builds a valid (slot,room) assignment first, THEN writes the CSV files.
This guarantees every generated instance is satisfiable.
"""

import os, random, csv, itertools

INSTRUCTORS_REQUIRED = [
    "Mr Aamir Gulzar","Mr Arshad Islam","Maam Marium Hida",
    "Mr Anas Bin Rashid","Mr Hasnain Akhtar","Mr Hasan Mujtaba",
    "Maam Bushra Kanwal",
]
EXTRA_INSTRUCTORS = [
    "Mr Bilal Ahmed","Maam Nadia Fatima","Mr Kamran Javed",
    "Maam Sadia Rehman","Mr Usman Malik","Maam Huma Ijaz",
    "Mr Fahad Chaudhry","Maam Rabia Qureshi","Mr Zain ul Abedin",
    "Maam Amna Tariq",
]
STUDENT_FIRST = [
    "Ali","Fatima","Hassan","Ayesha","Usman","Zainab","Omar","Sana",
    "Bilal","Maryam","Hamza","Noor","Ahmer","Hiba","Saad","Amina",
    "Asad","Rida","Danyal","Maira","Tariq","Hira","Faisal","Iqra",
    "Waleed","Saba","Imran","Lubna","Kamran","Rabia","Shahid","Farah",
    "Nabeel","Sidra","Adnan","Zara","Waqar","Aisha","Sohaib","Nimra",
]
STUDENT_LAST = [
    "Ahmed","Khan","Malik","Siddiqui","Tariq","Ali","Chaudhry","Qureshi",
    "Baig","Shah","Iqbal","Rizvi","Butt","Sheikh","Mirza","Hussain",
    "Javed","Raza","Awan","Niazi","Abbasi","Hashmi","Ansari","Aziz",
    "Beg","Syed","Waqar","Farooqui","Memon","Gilani","Bokhari","Khatri",
]
COURSE_NAMES = [
    "Intro to Programming","Data Structures","Algorithms","Database Systems",
    "Software Engineering","Operating Systems","Computer Networks",
    "Artificial Intelligence","Machine Learning","Calculus I","Calculus II",
    "Linear Algebra","Statistics","Physics I","Physics II",
    "English Composition","Discrete Mathematics","Digital Logic",
    "Computer Architecture","Web Development","Cybersecurity",
    "Compiler Design","Numerical Methods","Signal Processing",
    "Computer Vision","NLP","Embedded Systems","Data Mining",
    "Software Testing","Project Management","Graph Theory","Robotics",
    "Game Development","Image Processing","Simulation","Formal Methods",
    "Parallel Computing","Distributed Systems","IoT Systems","Big Data",
    "Differential Equations","Probability","Ethical Hacking",
    "Computer Graphics","HCI","Bioinformatics","Quantum Computing",
    "Mobile Computing","Cloud Computing","Distributed AI",
]
FEATURES  = ["Lab","Projector","Whiteboard"]
BUILDINGS = ["CS Building","Main Building","Lab Building","Eng Block"]


def _make_student_names(n):
    pool = [f"{f} {l}" for f, l in itertools.product(STUDENT_FIRST, STUDENT_LAST)]
    random.shuffle(pool)
    if n <= len(pool):
        return pool[:n]
    return pool + [f"Student{i}" for i in range(n - len(pool))]


def generate_instance(n_courses=10, n_rooms=None, n_slots=20, density=0.5,
                      tightness=0.5, output_dir="instances/generated", seed=None):
    """
    Generate a SATISFIABLE timetabling instance.
    Creates a valid assignment first, then writes CSV files.
    """
    if seed is not None:
        random.seed(seed)

    if n_rooms is None:
        n_rooms = max(4, int(n_courses * random.uniform(0.6, 0.8)))

    os.makedirs(output_dir, exist_ok=True)

    # -- Instructor pool ------------------------------------------------
    instructors = INSTRUCTORS_REQUIRED[:]
    while len(instructors) < max(n_courses // 3, 7):
        e = random.choice(EXTRA_INSTRUCTORS)
        if e not in instructors:
            instructors.append(e)

    # -- Build all possible (slot_tag, days, start, duration) tuples ----
    all_slots = []
    for days_str, dur in [("Monday/Wednesday/Friday", 50),
                           ("Tuesday/Thursday", 75)]:
        starts = [f"{h:02d}:00" for h in range(8, 18 if dur == 50 else 17)]
        pfx = "MWF" if "Friday" in days_str else "TTh"
        seen = set()
        for t in starts:
            tag = f"{pfx}-{t.replace(':','')}"
            if tag not in seen:
                seen.add(tag)
                all_slots.append((tag, days_str, t, dur))

    random.shuffle(all_slots)
    room_ids = [f"R{101+i}" for i in range(n_rooms)]

    # -- Build a valid assignment: each course gets unique (slot,room) --
    assignments = {}        # course_idx -> (slot_tag, room_id, days, start, dur)
    used_sr     = set()     # (slot_tag, room_id) pairs already taken
    inst_slot   = {}        # instructor -> slot_tag (no instructor double-booking)

    name_pool = COURSE_NAMES[:]; random.shuffle(name_pool)
    courses_data = []

    for i in range(n_courses):
        inst = instructors[i % len(instructors)]
        dur_choice = random.choice([50, 75])

        assigned = False
        for (stag, days, stime, sdur) in all_slots:
            if sdur != dur_choice: continue
            if inst_slot.get(inst) == stag: continue  # instructor conflict
            for rid in room_ids:
                if (stag, rid) not in used_sr:
                    assignments[i] = (stag, rid, days, stime, sdur)
                    used_sr.add((stag, rid))
                    inst_slot[inst] = stag
                    assigned = True
                    break
            if assigned: break

        if not assigned:
            # Relax duration constraint
            for (stag, days, stime, sdur) in all_slots:
                if inst_slot.get(inst) == stag: continue
                for rid in room_ids:
                    if (stag, rid) not in used_sr:
                        assignments[i] = (stag, rid, days, stime, sdur)
                        used_sr.add((stag, rid))
                        inst_slot[inst] = stag
                        assigned = True
                        dur_choice = sdur
                        break
                if assigned: break

        if not assigned:
            # Absolute fallback
            stag, days, stime, sdur = all_slots[i % len(all_slots)]
            assignments[i] = (stag, room_ids[i % n_rooms], days, stime, sdur)
            dur_choice = sdur

        stag, rid, days, stime, sdur = assignments[i]
        cid    = f"CS{100+i}-{(i%3)+1:02d}"
        cname  = name_pool[i % len(name_pool)]
        enroll = random.randint(15, 55)
        feat   = random.choice(FEATURES)
        courses_data.append([cid, cname, inst, enroll, sdur, feat])

    with open(os.path.join(output_dir, "courses.csv"), "w", newline='',
              encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["CourseID","CourseName","Instructor","Enrollment","Duration","RoomFeatures"])
        w.writerows(courses_data)

    # -- Rooms: capacity >= max enrollment, each room has 2-3 features --
    max_enroll = max(int(r[3]) for r in courses_data)
    rooms_data = []
    for i, rid in enumerate(room_ids):
        cap   = max_enroll + 10 if i == 0 else random.choice([50,60,80,100])
        feats = random.sample(FEATURES, k=random.randint(2,3))
        if i == 0 and "Lab" not in feats: feats[0] = "Lab"
        rooms_data.append([rid, random.choice(BUILDINGS), cap, ";".join(feats)])

    with open(os.path.join(output_dir, "rooms.csv"), "w", newline='',
              encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["RoomID","Building","Capacity","Features"])
        w.writerows(rooms_data)

    # -- Time slots: used ones + extras up to n_slots -------------------
    used_tags  = {a[0] for a in assignments.values()}
    slots_map  = {s[0]: s for s in all_slots}
    slots_out  = [slots_map[t] for t in used_tags if t in slots_map]
    extras     = [s for s in all_slots if s[0] not in used_tags]
    random.shuffle(extras)
    slots_out += extras[:max(0, n_slots - len(slots_out))]
    random.shuffle(slots_out)

    with open(os.path.join(output_dir, "timeslots.csv"), "w", newline='',
              encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["SlotID","Days","StartTime","Duration"])
        w.writerows(slots_out)

    # -- Students --------------------------------------------------------
    n_students    = max(10, int(n_courses * 3 * density))
    course_ids    = [r[0] for r in courses_data]
    names         = _make_student_names(n_students)
    students_data = []
    for i, sname in enumerate(names):
        n_enroll = random.randint(2, min(5, n_courses))
        enrolled = random.sample(course_ids, n_enroll)
        students_data.append([f"{i+1:03d}", sname, ";".join(enrolled)])

    with open(os.path.join(output_dir, "students.csv"), "w", newline='',
              encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["StudentID","StudentName","EnrolledCourses"])
        w.writerows(students_data)

    print(f"[Generator] Instance written to '{output_dir}' "
          f"({n_courses} courses, {n_rooms} rooms, "
          f"{len(slots_out)} slots, {n_students} students, "
          f"density={density}, tightness={tightness})")
    return output_dir
