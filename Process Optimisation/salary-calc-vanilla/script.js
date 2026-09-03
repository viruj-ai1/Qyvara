const columns = [
    "S No", "UAN No", "Name of Employee", "Designation", "Emp ID",
    "Department", "ESIC No", "PAN No", "Aadhaar No", "Bank",
    "IFSC Code", "Account No.", "PF Eligible (Y/N)", "ENPF/VPF",
    "Pension Eligible (Y/N)", "ESIC Eligible (Y/N)"
];

let employees = [
    ["1", "101686670051", "M Latchi Raju", "Head-Finance", "VIRUJ/0001", "", "", "ACQPM2951C", "", "State Bank of India", "SBIN0017760", "20012766110", "Y", "Y", "N", "N"],
    ["2", "100398993804", "Veeravalli Vani", "Manager - Business Dev", "VIRUJ/0003", "", "", "ANVPV4013G", "", "IDFC First Bank", "IDFB0040101", "10125010172", "Y", "Y", "N", "N"],
    ["3", "101686670033", "Sudhakar Bhaskar Rao K", "Manager - Logistics", "VIRUJ/0002", "", "", "ASRPK5416P", "", "IDFC First Bank", "IDFB0040101", "10134292939", "Y", "Y", "N", "N"],
    ["4", "100247983706", "B Nagendra Babu", "Executive - Purchases", "VIRUJ/0006", "", "", "CADPB4971L", "", "IDFC First Bank", "IDFB0040101", "10125010151", "Y", "Y", "Y", "N"],
    ["5", "101686659937", "K Ramya Bharathi", "Asst Manager - Logistics", "VIRUJ/0004", "", "", "DWAPK0878M", "", "IDFC First Bank", "IDFB0040101", "10135254710", "Y", "Y", "N", "N"],
    ["6", "101586659944", "Uppasala Anand", "Manager - Accounts", "VIRUJ/0008", "", "", "AAVPU2016P", "", "IDFC First Bank", "IDFB0040101", "10125010183", "Y", "Y", "N", "N"],
    ["7", "101686670022", "M Shivanath", "Accounts Executive", "VIRUJ/0007", "", "", "BLZPM6479B", "", "IDFC First Bank", "IDFB0040101", "10135206197", "Y", "Y", "N", "N"],
    ["8", "101686659963", "Nagula Suresh", "Assistant", "VIRUJ/0005", "", "5217388813", "ANSPN1661P", "", "IDFC First Bank", "IDFB0080221", "10152520613", "Y", "Y", "N", "N"],
    ["9", "VPPL00000001", "Arigela Siva Sai Satwika", "Hardware Trainee", "VIRUJ/0010", "", "", "", "", "Indian Bank", "IDIB000S013", "7903571850", "N", "N", "N", "N"],
    ["10", "101836252587", "Pulla Lavanya", "Housekeeping", "VIRUJ/0011", "", "5218654598", "BMHPL3729E", "", "IDFC First Bank", "IDFB0040101", "10134310959", "Y", "Y", "Y", "Y"],
    
    // --- R & D Placeholder Divider ---
    ["---", "---", "-- R & D DEPARTMENT --", "---", "---", "---", "---", "---", "---", "---", "---", "---", "-", "-", "-", "-"],
    
    ["21", "100362424529", "Srikanth Viswanathan", "Head - HR", "VIRUJ/RD/0006", "HR & Administration", "", "AOOPS2190M", "", "HDFC Bank", "HDFC0000512", "05121610001750", "Y", "Y", "Y", "N"],
    ["22", "101116040732", "Guruprasad D", "Assistant Manager", "VIRUJ/RD/0007", "Analytical R & D", "", "CFVPD4317P", "", "IDFC First Bank", "IDFB0040101", "10135182925", "Y", "Y", "Y", "N"],
    ["23", "101686669928", "Padma Shada", "Housekeeping Maid", "VIRUJ/RD/0012", "HR & Administration", "5217388309", "", "", "Kotak Mahindra Bank", "KKBK0007457", "7545202073", "Y", "Y", "Y", "Y"],
    ["24", "100699005048", "Jaipal Danam", "Lab Assistant", "VIRUJ/RD/0031", "HR & Administration", "5205760803", "CEUPJ2557R", "", "State Bank of India", "SBIN0020076", "52210630629", "Y", "Y", "Y", "Y"],
    ["25", "101586704475", "R Sandeep", "Executive", "VIRUJ/RD/0050", "Analytical R & D", "", "DLPUR2376E", "", "IDFC First Bank", "IDFB0040101", "10134225076", "Y", "Y", "Y", "N"],
    ["26", "101776343894", "Pradip Ashok Dubale", "Junior Chemist", "VIRUJ/RD/0059", "Chemical R & D", "5219662743", "HBVRD1419M", "", "IDFC First Bank", "IDFB0080221", "10143848873", "Y", "Y", "Y", "N"],
    ["27", "101586201506", "Ravi Lahu Dede", "Junior Analyst", "VIRUJ/RD/0064", "Analytical R & D", "", "FLUPD0753F", "", "HDFC Bank", "HDFC0001041", "50100564681102", "Y", "Y", "Y", "N"],
    ["28", "102075943316", "Bagirthi Anila", "Junior Executive - DQA", "VIRUJ/RD/0065", "Development - QA", "5220828964", "DLGPA3794F", "", "State Bank of India", "SBIN0021496", "62441000676", "Y", "Y", "Y", "Y"],
    ["29", "102078018656", "Naveen Kumar P", "Junior Engineer", "VIRUJ/RD/0066", "Tech Transfer", "", "GBHPP5055A", "", "ICICI Bank", "ICIC0004634", "463401500471", "Y", "Y", "Y", "N"],
    ["30", "102013217967", "Aloka Kumar Lenka", "Junior Engineer", "VIRUJ/RD/0068", "Chemical R & D", "", "BKAPL3018C", "", "State Bank of India", "SBIN0006473", "33224572191", "Y", "Y", "Y", "N"],
    ["31", "101686669890", "Sivanjaneyulu D", "Senior Chemist", "VIRUJ/RD/0069", "Chemical R & D", "", "FBRPD7085J", "", "HDFC Bank", "HDFC0001041", "50100379005727", "Y", "Y", "Y", "N"],
    ["32", "102116104471", "Sri Venu N", "Junior Engineer - MTC", "VIRUJ/RD/0072", "Maintenance", "", "CYXPN5524M", "", "ICICI Bank", "ICIC0004634", "463401500470", "Y", "Y", "Y", "N"],
    ["33", "102133729768", "Kusumapriya T", "HR Executive", "VIRUJ/RD/0074", "HR & Administration", "", "BWMPT6115N", "", "ICICI Bank", "ICIC0004779", "477901500413", "Y", "Y", "Y", "N"],
    ["34", "102146410471", "Priti Santhosh Shelke", "Trainee - AR&D", "VIRUJ/RD/0076", "Analytical R & D", "5221559388", "TIIPS2988L", "", "Central Bank of India", "CBIN0282512", "5328778779", "Y", "Y", "Y", "Y"],
    ["35", "102146410485", "Chakkapalli Devi Sri Harsha", "Trainee - AR&D", "VIRUJ/RD/0077", "Analytical R & D", "5221559546", "BWMPH1852B", "", "Canara Bank", "CNRB0013822", "35352200005390", "Y", "Y", "Y", "Y"],
    ["36", "102149695102", "Amol Shinde", "Trainee - CRD", "VIRUJ/RD/0078", "Chemical R & D", "5221584779", "LXRPS8862P", "", "Pragathi Krishna Gramin Bank", "PKGB0011086", "11086101011128", "Y", "Y", "Y", "Y"],
    ["37", "10003423843", "T K Ramanjanelu", "Lab Assistant", "VIRUJ/RD/0079", "HR & Administration", "5203194071", "CFBPT2546A", "", "Union Bank of India", "UBIN0813109", "131010100179398", "Y", "Y", "Y", "Y"],
    ["38", "102179595639", "Manasi Naik", "Lab Assistant", "VIRUJ/RD/0080", "HR & Administration", "5221818193", "", "", "Punjab National Bank", "PUNB0222710", "2227101700003100", "Y", "Y", "Y", "Y"]
];

const tableBody = document.getElementById('tableBody');
const addRowBtn = document.getElementById('addRowBtn');
const saveDataBtn = document.getElementById('saveDataBtn');
const emptyState = document.getElementById('emptyState');

function renderTable() {
    tableBody.innerHTML = '';
    
    if (employees.length === 0) {
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');
    }

    employees.forEach((row, rowIndex) => {
        const tr = document.createElement('tr');
        
        row.forEach((cellContent, colIndex) => {
            const td = document.createElement('td');
            const input = document.createElement('input');
            input.type = 'text';
            input.value = cellContent;
            input.placeholder = '—';
            
            // Handle input parsing
            input.addEventListener('input', (e) => {
                employees[rowIndex][colIndex] = e.target.value;
            });
            
            td.appendChild(input);
            tr.appendChild(td);
        });
        
        // Delete button cell
        const tdAction = document.createElement('td');
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-icon';
        deleteBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>';
        deleteBtn.title = "Remove row";
        
        deleteBtn.onclick = () => {
            employees.splice(rowIndex, 1);
            renderTable();
        };
        
        tdAction.appendChild(deleteBtn);
        tr.appendChild(tdAction);
        
        tableBody.appendChild(tr);
    });
}

addRowBtn.addEventListener('click', () => {
    employees.push(Array(columns.length).fill(''));
    renderTable();
});

saveDataBtn.addEventListener('click', () => {
    console.log("Saved Employee Data:", employees);
    
    // Quick little animation effect to show save
    const originalText = saveDataBtn.innerHTML;
    saveDataBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg> Saved!';
    
    setTimeout(() => {
        saveDataBtn.innerHTML = originalText;
    }, 2000);
});

// Initial Render
renderTable();
