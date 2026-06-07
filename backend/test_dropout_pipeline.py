"""
Complete test script for Dropout Prediction Pipeline.

Run: python test_dropout_pipeline.py

This will:
1. Create 1 District + 1 Mandal + 1 School
2. Create 5 students (mix of risk profiles)
3. Add some attendance records
4. Run ML predictions
5. Show predictions + student_ml_input + student_predictions tables
6. Test all API endpoints
"""

import sys; sys.path.insert(0, '.')
import asyncio
import json
from datetime import date, timedelta
from random import random, choice

from app.database.session import AsyncSessionLocal
from app.models.school import District, Mandal, School
from app.models.student import Student, Gender
from app.models.attendance import Attendance, AttendanceStatus, AttendanceReferenceType
from app.models.assessment import Assessment, AssessmentResult, AssessmentType
from app.services.dropout_prediction_service import DropoutPredictionService


async def test_full_pipeline():
    print("\n" + "="*60)
    print("🧪 DROPOUT PREDICTION PIPELINE TEST")
    print("="*60)

    async with AsyncSessionLocal() as db:
        # ── STEP 1: Create Master Data ──
        print("\n📌 STEP 1: Creating master data...")
        
        d = District(name="Hyderabad District")
        db.add(d); await db.flush()
        print(f"  ✅ District created: id={d.id}")

        m = Mandal(name="Gachibowli Mandal", district_id=d.id)
        db.add(m); await db.flush()
        print(f"  ✅ Mandal created: id={m.id}")

        s = School(
            name="ZPHS Gachibowli", 
            dise_code="ZPHS001", 
            mandal_id=m.id, 
            district_id=d.id,
            has_computer_lab=True,
            has_electricity=True,
            has_library=True
        )
        db.add(s); await db.flush()
        print(f"  ✅ School created: id={s.id}")

        # ── STEP 2: Create Students ──
        print("\n📌 STEP 2: Creating 5 students with different profiles...")

        students_data = [
            # (admission_no, first_name, last_name, gender, class, dob, has_disability, scholarship, midday_meal)
            ("STU001", "Rahul", "Sharma", Gender.MALE,   9,  date(2011, 5, 10), False, True,  True),
            ("STU002", "Priya", "Verma",  Gender.FEMALE, 10, date(2010, 8, 15), False, True,  True),
            ("STU003", "Amit",  "Kumar",  Gender.MALE,   8,  date(2012, 3, 22), True,  False, True),
            ("STU004", "Suman", "Patel",  Gender.FEMALE, 9,  date(2011, 11, 5), False, True,  True),
            ("STU005", "Ravi",  "Reddy",  Gender.MALE,   10, date(2010, 7, 18), False, False, True),
        ]

        students = []
        for adm_no, fn, ln, gender, cls, dob, disability, scholar, meal in students_data:
            stu = Student(
                admission_no=adm_no,
                first_name=fn,
                last_name=ln,
                gender=gender,
                current_class=cls,
                date_of_birth=dob,
                school_id=s.id,
                academic_year="2025-26",
                has_disability=disability,
                receives_scholarship=scholar,
                receives_midday_meal=meal,
                is_active=True
            )
            db.add(stu)
            students.append(stu)
        
        await db.flush()
        for stu in students:
            print(f"  ✅ Student created: {stu.first_name} {stu.last_name} (id={stu.id}, class {stu.current_class})")

        # ── STEP 3: Add Attendance ──
        print("\n📌 STEP 3: Adding attendance records (mix of good/bad)...")

        statuses = [AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.HALF_DAY]
        
        for i, stu in enumerate(students):
            # Student 0 (Rahul): 90% attendance ← good
            # Student 1 (Priya): 85% attendance ← okay
            # Student 2 (Amit):  40% attendance ← bad (high risk)
            # Student 3 (Suman): 70% attendance ← medium
            # Student 4 (Ravi):  95% attendance ← good
            
            for day_offset in range(30):  # Last 30 days
                if i == 2:  # Amit — mostly absent
                    status = AttendanceStatus.ABSENT if random() < 0.6 else AttendanceStatus.PRESENT
                elif i == 3:  # Suman — mixed
                    status = AttendanceStatus.ABSENT if random() < 0.3 else AttendanceStatus.PRESENT
                else:  # Others — mostly present
                    status = AttendanceStatus.PRESENT if random() < 0.9 else AttendanceStatus.ABSENT

                att = Attendance(
                    reference_type=AttendanceReferenceType.STUDENT,
                    reference_id=stu.id,
                    date=date.today() - timedelta(days=day_offset),
                    status=status,
                    marked_by=0,
                    school_id=s.id,
                )
                db.add(att)
            
            print(f"  ✅ Attendance added for {stu.first_name}")

        # ── STEP 4: Add Assessments ──
        print("\n📌 STEP 4: Adding assessment results...")

        # Create one assessment
        assessment = Assessment(
            title="Mid-Term Exam 2025",
            assessment_type=AssessmentType.EXAM,
            max_marks=100,
            subject_name="Mathematics",
            class_id=stu.current_class,
            conducted_date=date.today() - timedelta(days=15),
            school_id=s.id,
        )
        db.add(assessment)
        await db.flush()

        marks_by_student = [92, 85, 25, 55, 95]  # Rahul=95%, Priya=85%, Amit=25%, Suman=55%, Ravi=95%
        for i, stu in enumerate(students):
            ar = AssessmentResult(
                student_id=stu.id,
                assessment_id=assessment.id,
                marks_obtained=marks_by_student[i],
                percentage=float(marks_by_student[i]),
                grade="A" if marks_by_student[i] >= 80 else "B" if marks_by_student[i] >= 60 else "C" if marks_by_student[i] >= 40 else "D",
                school_id=s.id,
            )
            db.add(ar)
            print(f"  ✅ Assessment added for {stu.first_name}: {marks_by_student[i]}%")

        await db.commit()
        print(f"\n{'='*60}")
        print("✅ MASTER DATA CREATED SUCCESSFULLY!")
        print(f"{'='*60}")

    # ── STEP 5: Run ML Predictions ──
    print(f"\n📌 STEP 5: Running ML Prediction Pipeline...")
    
    async with AsyncSessionLocal() as db:
        service = DropoutPredictionService(db)
        result = await service.run_predictions(school_id=s.id)
        await db.commit()

        print(f"\n{'='*60}")
        print("✅ PREDICTION RESULTS:")
        print(f"   Batch ID:        {result['batch_id']}")
        print(f"   Total Students:  {result['total_students']}")
        print(f"   Critical Risk:   {result['critical_risk_count']}")
        print(f"   High Risk:       {result['high_risk_count']}")
        print(f"   Medium Risk:     {result['medium_risk_count']}")
        print(f"   Low Risk:        {result['low_risk_count']}")
        print(f"{'='*60}")

    # ── STEP 6: Show Each Student's Prediction ──
    print(f"\n📌 STEP 6: Individual Student Predictions...")
    
    async with AsyncSessionLocal() as db:
        service = DropoutPredictionService(db)
        
        for stu in students:
            pred = await service.get_student_prediction(stu.id)
            if pred:
                print(f"\n  {pred['student_name']} (admission: {pred['admission_no']})")
                print(f"     Risk Level:        {pred['risk_level']}")
                print(f"     Dropout Probability: {pred['dropout_probability']:.2f}%")
                print(f"     Recommendation:    {pred['recommendation']}")

    print(f"\n{'='*60}")
    print("🎉 PIPELINE TEST COMPLETE!")
    print(f"{'='*60}")
    print(f"\nNext steps:")
    print(f"  1. Open Swagger: http://localhost:8000/docs")
    print(f"  2. Try these APIs:")
    print(f"     GET  /api/v1/dropout/high-risk")
    print(f"     GET  /api/v1/dropout/student/{students[0].id}")
    print(f"     GET  /api/v1/dropout/school/{s.id}")
    print(f"     GET  /api/v1/dropout/mandal/{m.id}")
    print(f"     GET  /api/v1/dropout/district/{d.id}")
    print(f"  3. Check student_ml_input and student_predictions tables in MySQL")
    print(f"  4. Or run mobile app: edu-governance-platform/mobile-app → npm start")


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())