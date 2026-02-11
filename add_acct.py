from app.dao.employee_dao import EmployeeDAO

employee = EmployeeDAO.create(
    employee_id='T0759',
    email='mike.tran@techvify.com.vn',
    password='123456',
    vn_full_name='Trần Lê Minh',
    en_full_name='Mike Tran',
    role='MEMBER',
    status=True
)


employee = EmployeeDAO.create(
    employee_id='T0760',
    email='brian.nguyen@techvify.com.vn',
    password='123456',
    vn_full_name='Nguyễn Bá Mạnh Kiệt',
    en_full_name='Brian Nguyen',
    role='ADMIN',
    status=True
)