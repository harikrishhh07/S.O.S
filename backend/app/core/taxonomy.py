"""
S.O.S. Campus Service Taxonomy
Full 24-department hierarchy used for report categorization and routing.
"""

# Each entry: { "id": str, "label": str, "services": [{ "id": str, "label": str }] }
DEPARTMENTS = [
    {
        "id": "architect_services",
        "label": "Architect Services",
        "services": [
            {"id": "new_facility_furniture", "label": "Furniture & Fixtures (New Facility)"},
            {"id": "new_facility_interior", "label": "Interior Modification (New Facility)"},
            {"id": "new_facility_layout", "label": "Layout Planning"},
            {"id": "new_facility_civil", "label": "Civil Works (New Facility)"},
            {"id": "new_facility_other", "label": "Other Requirements (New Facility)"},
            {"id": "new_facility_escalator", "label": "Escalator / Lift Works"},
            {"id": "renovation_furniture", "label": "Furniture & Fixtures (Renovation)"},
            {"id": "renovation_interior", "label": "Interior Modification (Renovation)"},
            {"id": "renovation_layout", "label": "Layout Changes (Renovation)"},
            {"id": "renovation_civil", "label": "Civil Works (Renovation)"},
            {"id": "renovation_other", "label": "Other Requirements (Renovation)"},
        ],
    },
    {
        "id": "facility_services",
        "label": "Facility Services",
        "services": [
            {"id": "facility_cctv_telecom", "label": "CCTV & Telecom"},
            {"id": "facility_civil", "label": "Civil Works"},
            {"id": "facility_electrical", "label": "Electrical Works"},
            {"id": "facility_fire_safety", "label": "Fire & Safety"},
            {"id": "facility_housekeeping", "label": "Housekeeping"},
            {"id": "facility_hvac", "label": "HVAC / Air Conditioning"},
            {"id": "facility_plumbing", "label": "Plumbing"},
            {"id": "facility_lift_escalator", "label": "Lift / Escalator Maintenance"},
            {"id": "facility_general", "label": "General Maintenance"},
        ],
    },
    {
        "id": "hostel_services",
        "label": "Hostel Services",
        "services": [
            {"id": "hostel_civil", "label": "Civil"},
            {"id": "hostel_electrical", "label": "Electrical"},
            {"id": "hostel_housekeeping", "label": "Housekeeping"},
            {"id": "hostel_laundry", "label": "Laundry"},
            {"id": "hostel_mess", "label": "Mess / Food Services"},
            {"id": "hostel_security", "label": "Security"},
            {"id": "hostel_plumbing", "label": "Plumbing"},
            {"id": "hostel_ac_hvac", "label": "AC / HVAC"},
            {"id": "hostel_pest_control", "label": "Pest Control"},
            {"id": "hostel_maintenance", "label": "Hostel Maintenance"},
        ],
    },
    {
        "id": "transport_services",
        "label": "Transport Services",
        "services": [
            {"id": "transport_buses", "label": "College Buses"},
            {"id": "transport_route_mgmt", "label": "Bus Route Management"},
            {"id": "transport_student", "label": "Student Transportation"},
            {"id": "transport_faculty_staff", "label": "Faculty / Staff Transportation"},
            {"id": "transport_vehicle_maintenance", "label": "Vehicle Maintenance"},
            {"id": "transport_driver", "label": "Driver Services"},
            {"id": "transport_security", "label": "Transport Security"},
        ],
    },
    {
        "id": "security_services",
        "label": "Security Services",
        "services": [
            {"id": "security_main_gate", "label": "Main Gate Security"},
            {"id": "security_hostel", "label": "Hostel Security"},
            {"id": "security_academic", "label": "Academic Block Security"},
            {"id": "security_cctv_monitoring", "label": "CCTV Monitoring"},
            {"id": "security_visitor", "label": "Visitor Management"},
            {"id": "security_vehicle_parking", "label": "Vehicle / Parking Security"},
            {"id": "security_emergency", "label": "Emergency Response"},
            {"id": "security_access_control", "label": "Access Control"},
        ],
    },
    {
        "id": "housekeeping_services",
        "label": "Housekeeping Services",
        "services": [
            {"id": "hk_academic_blocks", "label": "Academic Blocks"},
            {"id": "hk_admin_buildings", "label": "Administrative Buildings"},
            {"id": "hk_hostels", "label": "Hostels"},
            {"id": "hk_laboratories", "label": "Laboratories"},
            {"id": "hk_classrooms", "label": "Classrooms"},
            {"id": "hk_washrooms", "label": "Washrooms"},
            {"id": "hk_common_areas", "label": "Common Areas"},
            {"id": "hk_waste_collection", "label": "Waste Collection"},
            {"id": "hk_deep_cleaning", "label": "Deep Cleaning"},
        ],
    },
    {
        "id": "electrical_services",
        "label": "Electrical Services",
        "services": [
            {"id": "elec_maintenance", "label": "Electrical Maintenance"},
            {"id": "elec_power_supply", "label": "Power Supply"},
            {"id": "elec_generators", "label": "Generators"},
            {"id": "elec_ups", "label": "UPS"},
            {"id": "elec_lighting", "label": "Lighting"},
            {"id": "elec_panels", "label": "Electrical Panels"},
            {"id": "elec_wiring_cabling", "label": "Wiring / Cabling"},
            {"id": "elec_emergency_repairs", "label": "Emergency Electrical Repairs"},
        ],
    },
    {
        "id": "civil_plumbing_services",
        "label": "Civil & Plumbing Services",
        "services": [
            {"id": "civil_building_repairs", "label": "Building Repairs"},
            {"id": "civil_walls_flooring", "label": "Walls / Flooring"},
            {"id": "civil_doors_windows", "label": "Doors & Windows"},
            {"id": "civil_roofing", "label": "Roofing"},
            {"id": "civil_plumbing", "label": "Plumbing"},
            {"id": "civil_water_supply", "label": "Water Supply"},
            {"id": "civil_drainage", "label": "Drainage"},
            {"id": "civil_sanitary_fixtures", "label": "Sanitary Fixtures"},
            {"id": "civil_leakage_repairs", "label": "Leakage Repairs"},
        ],
    },
    {
        "id": "fire_safety_services",
        "label": "Fire & Safety Services",
        "services": [
            {"id": "fire_extinguishers", "label": "Fire Extinguishers"},
            {"id": "fire_alarm_systems", "label": "Fire Alarm Systems"},
            {"id": "fire_hydrants", "label": "Fire Hydrants"},
            {"id": "fire_sprinklers", "label": "Sprinkler Systems"},
            {"id": "fire_emergency_exits", "label": "Emergency Exits"},
            {"id": "fire_inspections", "label": "Fire Safety Inspections"},
            {"id": "fire_drills", "label": "Emergency Drills"},
            {"id": "fire_safety_equipment", "label": "Safety Equipment"},
        ],
    },
    {
        "id": "hvac_ac_services",
        "label": "HVAC / AC Services",
        "services": [
            {"id": "hvac_ac", "label": "Air Conditioning"},
            {"id": "hvac_maintenance", "label": "HVAC Maintenance"},
            {"id": "hvac_ac_repair", "label": "AC Repair"},
            {"id": "hvac_ac_installation", "label": "AC Installation"},
            {"id": "hvac_ventilation", "label": "Ventilation"},
            {"id": "hvac_duct_maintenance", "label": "Duct Maintenance"},
            {"id": "hvac_temp_control", "label": "Temperature Control"},
        ],
    },
    {
        "id": "it_telecom_services",
        "label": "IT & Telecom Services",
        "services": [
            {"id": "it_wifi", "label": "Campus Wi-Fi"},
            {"id": "it_internet_network", "label": "Internet / Network"},
            {"id": "it_lan", "label": "LAN"},
            {"id": "it_telephone_epabx", "label": "Telephone / EPABX"},
            {"id": "it_cctv_network", "label": "CCTV Network"},
            {"id": "it_network_maintenance", "label": "Network Maintenance"},
            {"id": "it_infrastructure", "label": "IT Infrastructure"},
            {"id": "it_hardware_support", "label": "Computer / Hardware Support"},
        ],
    },
    {
        "id": "laundry_services",
        "label": "Laundry Services",
        "services": [
            {"id": "laundry_hostel", "label": "Hostel Laundry"},
            {"id": "laundry_washing", "label": "Washing"},
            {"id": "laundry_drying", "label": "Drying"},
            {"id": "laundry_ironing", "label": "Ironing"},
            {"id": "laundry_collection_delivery", "label": "Laundry Collection / Delivery"},
            {"id": "laundry_equipment_maintenance", "label": "Laundry Equipment Maintenance"},
        ],
    },
    {
        "id": "mess_food_services",
        "label": "Mess / Food Services",
        "services": [
            {"id": "mess_hostel", "label": "Hostel Mess"},
            {"id": "mess_food_prep", "label": "Food Preparation"},
            {"id": "mess_dining_hall", "label": "Dining Hall"},
            {"id": "mess_kitchen_maintenance", "label": "Kitchen Maintenance"},
            {"id": "mess_drinking_water", "label": "Drinking Water"},
            {"id": "mess_food_hygiene", "label": "Food Hygiene"},
            {"id": "mess_waste_management", "label": "Waste Management"},
            {"id": "mess_catering_events", "label": "Catering / Events"},
        ],
    },
    {
        "id": "transport_parking",
        "label": "Transport & Parking",
        "services": [
            {"id": "parking_student", "label": "Student Parking"},
            {"id": "parking_faculty_staff", "label": "Faculty / Staff Parking"},
            {"id": "parking_visitor", "label": "Visitor Parking"},
            {"id": "parking_two_wheeler", "label": "Two-Wheeler Parking"},
            {"id": "parking_four_wheeler", "label": "Four-Wheeler Parking"},
            {"id": "parking_security", "label": "Parking Security"},
            {"id": "parking_traffic_mgmt", "label": "Traffic Management"},
        ],
    },
    {
        "id": "landscaping_campus",
        "label": "Landscaping & Campus Maintenance",
        "services": [
            {"id": "landscape_gardening", "label": "Gardening"},
            {"id": "landscape_lawn", "label": "Lawn Maintenance"},
            {"id": "landscape_tree", "label": "Tree Maintenance"},
            {"id": "landscape_landscaping", "label": "Landscaping"},
            {"id": "landscape_irrigation", "label": "Irrigation"},
            {"id": "landscape_cleanliness", "label": "Campus Cleanliness"},
            {"id": "landscape_pest_control", "label": "Pest Control"},
            {"id": "landscape_outdoor", "label": "Outdoor Area Maintenance"},
        ],
    },
    {
        "id": "waste_management",
        "label": "Waste Management",
        "services": [
            {"id": "waste_solid", "label": "Solid Waste Collection"},
            {"id": "waste_wet", "label": "Wet Waste"},
            {"id": "waste_dry", "label": "Dry Waste"},
            {"id": "waste_ewaste", "label": "E-Waste"},
            {"id": "waste_biomedical", "label": "Biomedical / Laboratory Waste"},
            {"id": "waste_recycling", "label": "Recycling"},
            {"id": "waste_segregation", "label": "Waste Segregation"},
            {"id": "waste_disposal", "label": "Disposal"},
        ],
    },
    {
        "id": "student_admin_services",
        "label": "Student / Administrative Services",
        "services": [
            {"id": "admin_admissions", "label": "Admissions"},
            {"id": "admin_student_affairs", "label": "Student Affairs"},
            {"id": "admin_academic", "label": "Academic Administration"},
            {"id": "admin_examination", "label": "Examination"},
            {"id": "admin_accounts_finance", "label": "Accounts / Finance"},
            {"id": "admin_scholarships", "label": "Scholarships"},
            {"id": "admin_certificates", "label": "Certificates / Documents"},
            {"id": "admin_id_cards", "label": "ID Cards"},
            {"id": "admin_grievances", "label": "Grievances"},
        ],
    },
    {
        "id": "medical_health_services",
        "label": "Medical / Health Services",
        "services": [
            {"id": "medical_centre", "label": "Campus Medical Centre"},
            {"id": "medical_first_aid", "label": "First Aid"},
            {"id": "medical_consultation", "label": "Doctor / Medical Consultation"},
            {"id": "medical_emergency", "label": "Emergency Medical Support"},
            {"id": "medical_ambulance", "label": "Ambulance"},
            {"id": "medical_health_camps", "label": "Health Camps"},
            {"id": "medical_pharmacy", "label": "Pharmacy / Medicines"},
        ],
    },
    {
        "id": "library_services",
        "label": "Library Services",
        "services": [
            {"id": "library_books", "label": "Book Services"},
            {"id": "library_digital", "label": "Digital Library"},
            {"id": "library_journals", "label": "Journals / Research Papers"},
            {"id": "library_reading_rooms", "label": "Reading Rooms"},
            {"id": "library_computers", "label": "Computer / Internet Facilities"},
            {"id": "library_issue_return", "label": "Book Issue / Return"},
            {"id": "library_maintenance", "label": "Library Maintenance"},
        ],
    },
    {
        "id": "sports_recreation",
        "label": "Sports & Recreation",
        "services": [
            {"id": "sports_indoor", "label": "Indoor Sports"},
            {"id": "sports_outdoor", "label": "Outdoor Sports"},
            {"id": "sports_gym", "label": "Gymnasium"},
            {"id": "sports_grounds", "label": "Sports Grounds"},
            {"id": "sports_equipment", "label": "Sports Equipment"},
            {"id": "sports_swimming", "label": "Swimming Pool / Aquatic Facilities"},
            {"id": "sports_events", "label": "Sports Events"},
            {"id": "sports_maintenance", "label": "Maintenance"},
        ],
    },
    {
        "id": "labs_technical",
        "label": "Laboratories & Technical Facilities",
        "services": [
            {"id": "lab_equipment", "label": "Laboratory Equipment"},
            {"id": "lab_equipment_maintenance", "label": "Equipment Maintenance"},
            {"id": "lab_electrical_electronic", "label": "Electrical / Electronic Labs"},
            {"id": "lab_computer", "label": "Computer Labs"},
            {"id": "lab_mechanical", "label": "Mechanical Labs"},
            {"id": "lab_civil", "label": "Civil Labs"},
            {"id": "lab_chemical_science", "label": "Chemical / Science Labs"},
            {"id": "lab_safety_equipment", "label": "Safety Equipment"},
        ],
    },
    {
        "id": "procurement_stores",
        "label": "Procurement / Stores",
        "services": [
            {"id": "proc_purchase_requests", "label": "Purchase Requests"},
            {"id": "proc_vendor_mgmt", "label": "Vendor Management"},
            {"id": "proc_material", "label": "Material Procurement"},
            {"id": "proc_inventory", "label": "Inventory"},
            {"id": "proc_stock_mgmt", "label": "Stock Management"},
            {"id": "proc_equipment", "label": "Equipment Procurement"},
            {"id": "proc_furniture", "label": "Furniture Procurement"},
            {"id": "proc_stationery", "label": "Stationery"},
        ],
    },
    {
        "id": "environment_sustainability",
        "label": "Environment & Sustainability",
        "services": [
            {"id": "env_solar_renewable", "label": "Solar / Renewable Energy"},
            {"id": "env_rainwater", "label": "Rainwater Harvesting"},
            {"id": "env_water_conservation", "label": "Water Conservation"},
            {"id": "env_waste_mgmt", "label": "Waste Management"},
            {"id": "env_energy_mgmt", "label": "Energy Management"},
            {"id": "env_green_campus", "label": "Green Campus"},
            {"id": "env_monitoring", "label": "Environmental Monitoring"},
        ],
    },
    {
        "id": "events_campus_facilities",
        "label": "Events & Campus Facilities",
        "services": [
            {"id": "events_auditorium", "label": "Auditorium"},
            {"id": "events_seminar_halls", "label": "Seminar Halls"},
            {"id": "events_conference_rooms", "label": "Conference Rooms"},
            {"id": "events_setup", "label": "Event Setup"},
            {"id": "events_av_equipment", "label": "Stage / Audio-Visual Equipment"},
            {"id": "events_furniture", "label": "Furniture Arrangement"},
            {"id": "events_electrical_lighting", "label": "Electrical / Lighting Support"},
            {"id": "events_security", "label": "Event Security"},
            {"id": "events_housekeeping", "label": "Housekeeping"},
        ],
    },
]

# Flat lookup maps
DEPARTMENT_IDS = [d["id"] for d in DEPARTMENTS]
DEPARTMENT_LABELS = {d["id"]: d["label"] for d in DEPARTMENTS}

# service_id -> department_id reverse map
SERVICE_TO_DEPARTMENT: dict[str, str] = {}
for _dept in DEPARTMENTS:
    for _svc in _dept["services"]:
        SERVICE_TO_DEPARTMENT[_svc["id"]] = _dept["id"]

ALL_SERVICE_IDS = list(SERVICE_TO_DEPARTMENT.keys())
SERVICE_LABELS = {
    svc["id"]: svc["label"]
    for dept in DEPARTMENTS
    for svc in dept["services"]
}

# Safety-critical department ids (alerts go to Security + Admin immediately)
SAFETY_CRITICAL_DEPARTMENTS = {
    "security_services",
    "fire_safety_services",
    "electrical_services",
    "medical_health_services",
}
