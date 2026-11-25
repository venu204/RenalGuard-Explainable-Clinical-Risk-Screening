"""Patient intelligence directory and registration workflow."""
from __future__ import annotations

from datetime import datetime

import streamlit as st

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api_client import get_json, post, handle
from ui import page_intro, render_patient_card


def show():
    page_intro("PATIENT INTELLIGENCE", "Patient directory", "Search patient profiles, review their latest risk signals, and start the next clinical action.")
    directory, register = st.tabs(["Patient intelligence", "Add patient"])

    with directory:
        try:
            patients = get_json("/patients")
        except Exception as error:
            st.error(f"Unable to load patients: {error}")
            return
        search = st.text_input("Search patient", placeholder="Search by name or patient ID", key="patient_search")
        filtered = [patient for patient in patients if search.lower() in patient["full_name"].lower() or search.lower() in patient["patient_code"].lower()]
        st.caption(f"{len(filtered)} patient profile(s) shown · Open History to load a patient’s latest clinical values.")
        if not filtered:
            st.info("No patient matches this search. Add a patient or clear the search.")
        for patient in filtered:
            # Avoid a history request for every card. Details load only when the
            # clinician opens that patient's History or Assessment workflow.
            render_patient_card(patient)
            action1, action2, action3, _ = st.columns([1, 1, 1, 3])
            if action1.button("Assess", key=f"assess_{patient['id']}", type="primary", use_container_width=True):
                st.session_state.selected_patient_id = patient["id"]
                st.session_state.page = "Screening Queue"
                st.rerun()
            if action2.button("History", key=f"history_{patient['id']}", use_container_width=True):
                st.session_state.selected_patient_id = patient["id"]
                st.session_state.page = "Clinical Insights"
                st.rerun()
            if action3.button("Simulate", key=f"sim_{patient['id']}", use_container_width=True):
                st.session_state.selected_patient_id = patient["id"]
                st.session_state.page = "Simulations"
                st.rerun()

    with register:
        st.markdown("<div class='rg-card'><div class='rg-section-title'>New patient profile</div><div class='rg-section-caption'>Create a clinical profile before recording a screening visit.</div>", unsafe_allow_html=True)
        with st.form("new_patient_form", clear_on_submit=True):
            first, second = st.columns(2)
            full_name = first.text_input("Full name *", placeholder="Patient name")
            gender = second.selectbox("Gender *", ["MALE", "FEMALE", "OTHER"])
            third, fourth = st.columns(2)
            dob = third.date_input("Date of birth *", min_value=datetime(1900, 1, 1).date(), max_value=datetime.today().date())
            contact = fourth.text_input("Contact number", placeholder="Optional")
            submitted = st.form_submit_button("Create patient profile", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if submitted:
            if not full_name.strip():
                st.error("Enter the patient’s full name.")
                return
            try:
                result = handle(post("/patients", {"full_name": full_name.strip(), "date_of_birth": datetime.combine(dob, datetime.min.time()).isoformat(), "gender": gender, "contact_number": contact.strip() or None}))
                st.success(f"Patient profile created: {result['patient_code']} — {result['full_name']}")
            except Exception as error:
                st.error(f"Could not create patient: {error}")
