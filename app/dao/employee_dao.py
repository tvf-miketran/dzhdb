from app.models.employee import Employee

class EmployeeDAO:

    @staticmethod
    def get_by_employee_id(employee_id: str):
        return Employee.query.filter_by(employeeId=employee_id).first()