from django.utils import timezone
def eligibility(student,job):
    reasons=[]
    if job.passing_year and student.passing_year!=job.passing_year: reasons.append(f'Passing year must be {job.passing_year}.')
    branches=[x.strip().lower() for x in job.eligible_branches.split(',') if x.strip()]
    if branches and student.branch.lower() not in branches: reasons.append('Your branch is not eligible.')
    if job.min_cgpa is not None and (student.cgpa is None or student.cgpa<job.min_cgpa): reasons.append(f'Minimum CGPA required: {job.min_cgpa}.')
    if student.active_backlogs>job.max_backlogs: reasons.append(f'Maximum active backlogs allowed: {job.max_backlogs}.')
    skills={x.strip().lower() for x in student.skills.split(',') if x.strip()}
    missing={x.strip().lower() for x in job.required_skills.split(',') if x.strip()}-skills
    if missing: reasons.append('Missing skills: '+', '.join(sorted(missing)))
    if job.deadline and job.deadline<timezone.localdate(): reasons.append('Application deadline has passed.')
    return {'eligible':not reasons,'reasons':reasons}
