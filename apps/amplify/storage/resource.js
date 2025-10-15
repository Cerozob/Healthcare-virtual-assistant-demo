"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.storage = void 0;
const backend_1 = require("@aws-amplify/backend");
exports.storage = (0, backend_1.defineStorage)({
    name: 'healthcareDocuments',
    access: (allow) => ({
        // Public documents - anyone can read, authenticated users can upload
        'public/*': [
            allow.guest.to(['read']),
            allow.authenticated.to(['read', 'write', 'delete'])
        ],
        // Patient-specific documents - only authenticated users can access
        'patients/{patient_id}/*': [
            allow.authenticated.to(['read', 'write', 'delete'])
        ],
        // Chat session documents - only authenticated users can access
        'chat-sessions/{session_id}/*': [
            allow.authenticated.to(['read', 'write', 'delete'])
        ],
        // Processed documents - only authenticated users can read
        'processed/*': [
            allow.authenticated.to(['read'])
        ],
        // Temporary uploads - authenticated users can upload, system can process
        'temp-uploads/*': [
            allow.authenticated.to(['read', 'write', 'delete'])
        ]
    })
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoicmVzb3VyY2UuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyJyZXNvdXJjZS50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7QUFBQSxrREFBcUQ7QUFFeEMsUUFBQSxPQUFPLEdBQUcsSUFBQSx1QkFBYSxFQUFDO0lBQ25DLElBQUksRUFBRSxxQkFBcUI7SUFDM0IsTUFBTSxFQUFFLENBQUMsS0FBSyxFQUFFLEVBQUUsQ0FBQyxDQUFDO1FBQ2xCLHFFQUFxRTtRQUNyRSxVQUFVLEVBQUU7WUFDVixLQUFLLENBQUMsS0FBSyxDQUFDLEVBQUUsQ0FBQyxDQUFDLE1BQU0sQ0FBQyxDQUFDO1lBQ3hCLEtBQUssQ0FBQyxhQUFhLENBQUMsRUFBRSxDQUFDLENBQUMsTUFBTSxFQUFFLE9BQU8sRUFBRSxRQUFRLENBQUMsQ0FBQztTQUNwRDtRQUVELG1FQUFtRTtRQUNuRSx5QkFBeUIsRUFBRTtZQUN6QixLQUFLLENBQUMsYUFBYSxDQUFDLEVBQUUsQ0FBQyxDQUFDLE1BQU0sRUFBRSxPQUFPLEVBQUUsUUFBUSxDQUFDLENBQUM7U0FDcEQ7UUFFRCwrREFBK0Q7UUFDL0QsOEJBQThCLEVBQUU7WUFDOUIsS0FBSyxDQUFDLGFBQWEsQ0FBQyxFQUFFLENBQUMsQ0FBQyxNQUFNLEVBQUUsT0FBTyxFQUFFLFFBQVEsQ0FBQyxDQUFDO1NBQ3BEO1FBRUQsMERBQTBEO1FBQzFELGFBQWEsRUFBRTtZQUNiLEtBQUssQ0FBQyxhQUFhLENBQUMsRUFBRSxDQUFDLENBQUMsTUFBTSxDQUFDLENBQUM7U0FDakM7UUFFRCx5RUFBeUU7UUFDekUsZ0JBQWdCLEVBQUU7WUFDaEIsS0FBSyxDQUFDLGFBQWEsQ0FBQyxFQUFFLENBQUMsQ0FBQyxNQUFNLEVBQUUsT0FBTyxFQUFFLFFBQVEsQ0FBQyxDQUFDO1NBQ3BEO0tBQ0YsQ0FBQztDQUNILENBQUMsQ0FBQyIsInNvdXJjZXNDb250ZW50IjpbImltcG9ydCB7IGRlZmluZVN0b3JhZ2UgfSBmcm9tICdAYXdzLWFtcGxpZnkvYmFja2VuZCc7XG5cbmV4cG9ydCBjb25zdCBzdG9yYWdlID0gZGVmaW5lU3RvcmFnZSh7XG4gIG5hbWU6ICdoZWFsdGhjYXJlRG9jdW1lbnRzJyxcbiAgYWNjZXNzOiAoYWxsb3cpID0+ICh7XG4gICAgLy8gUHVibGljIGRvY3VtZW50cyAtIGFueW9uZSBjYW4gcmVhZCwgYXV0aGVudGljYXRlZCB1c2VycyBjYW4gdXBsb2FkXG4gICAgJ3B1YmxpYy8qJzogW1xuICAgICAgYWxsb3cuZ3Vlc3QudG8oWydyZWFkJ10pLFxuICAgICAgYWxsb3cuYXV0aGVudGljYXRlZC50byhbJ3JlYWQnLCAnd3JpdGUnLCAnZGVsZXRlJ10pXG4gICAgXSxcbiAgICBcbiAgICAvLyBQYXRpZW50LXNwZWNpZmljIGRvY3VtZW50cyAtIG9ubHkgYXV0aGVudGljYXRlZCB1c2VycyBjYW4gYWNjZXNzXG4gICAgJ3BhdGllbnRzL3twYXRpZW50X2lkfS8qJzogW1xuICAgICAgYWxsb3cuYXV0aGVudGljYXRlZC50byhbJ3JlYWQnLCAnd3JpdGUnLCAnZGVsZXRlJ10pXG4gICAgXSxcbiAgICBcbiAgICAvLyBDaGF0IHNlc3Npb24gZG9jdW1lbnRzIC0gb25seSBhdXRoZW50aWNhdGVkIHVzZXJzIGNhbiBhY2Nlc3NcbiAgICAnY2hhdC1zZXNzaW9ucy97c2Vzc2lvbl9pZH0vKic6IFtcbiAgICAgIGFsbG93LmF1dGhlbnRpY2F0ZWQudG8oWydyZWFkJywgJ3dyaXRlJywgJ2RlbGV0ZSddKVxuICAgIF0sXG4gICAgXG4gICAgLy8gUHJvY2Vzc2VkIGRvY3VtZW50cyAtIG9ubHkgYXV0aGVudGljYXRlZCB1c2VycyBjYW4gcmVhZFxuICAgICdwcm9jZXNzZWQvKic6IFtcbiAgICAgIGFsbG93LmF1dGhlbnRpY2F0ZWQudG8oWydyZWFkJ10pXG4gICAgXSxcbiAgICBcbiAgICAvLyBUZW1wb3JhcnkgdXBsb2FkcyAtIGF1dGhlbnRpY2F0ZWQgdXNlcnMgY2FuIHVwbG9hZCwgc3lzdGVtIGNhbiBwcm9jZXNzXG4gICAgJ3RlbXAtdXBsb2Fkcy8qJzogW1xuICAgICAgYWxsb3cuYXV0aGVudGljYXRlZC50byhbJ3JlYWQnLCAnd3JpdGUnLCAnZGVsZXRlJ10pXG4gICAgXVxuICB9KVxufSk7XG4iXX0=