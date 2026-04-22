import argparse
import os
import hashlib
import time
from bs4 import BeautifulSoup

def generate_unique_id(input_file: str) -> str:
    """Generate unique identifier based on filename, content hash and timestamp
    根據檔案名、內容雜湊和時間戳生成唯一識別符"""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            # Read part of the file to calculate hash value
            # 取檔案內容的一部分來計算雜湊值
            content = f.read(10000)  # Only read first 10000 characters for efficiency
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        
        # Combine filename, content hash and timestamp
        # 結合檔案名、內容雜湊和時間戳
        filename = os.path.basename(input_file).split('.')[0]  # Remove extension
        timestamp = str(int(time.time()))
        return f"{filename}_{content_hash}_{timestamp}"
    except Exception as e:
        # Fallback to using timestamp as unique ID if error occurs
        # 如果出錯，退回到使用時間戳作為唯一ID
        print(f"Error generating identifier: {e}")
        return f"autosave_{int(time.time())}"

def generate_script_js(identifier: str) -> str:
    """Generate JavaScript code for adding a Check column with autosave and export functionality."""
    # Avoid using template strings, write JavaScript code directly
    # 避免使用模板字符串，直接寫入JavaScript代碼
    script = """
    <script src='https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js'></script>
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        // Use provided unique identifier
        // 使用提供的唯一識別符
        const storageKey = "check_column_autosave_""" + identifier + """";
        console.log("Storage identifier in use:", storageKey);
        
        // For tracking last save time
        // 用於追蹤最後儲存時間
        const lastSaveTimeKey = storageKey + "_last_save_time";
        let lastSaveTime = parseInt(localStorage.getItem(lastSaveTimeKey) || "0");
        let saveStatusSpan; // Will be initialized later
        let saveBtn; // Will be initialized later
        
        // Update save time display
        // 更新儲存時間的顯示
        function updateSaveTimeDisplay() {
            if (!saveStatusSpan) return; // Ensure element is initialized
            
            if (lastSaveTime === 0) {
                saveStatusSpan.textContent = "Not saved yet";
                return;
            }
            
            const now = Math.floor(Date.now() / 1000);
            const diffSeconds = now - lastSaveTime;
            
            if (diffSeconds < 60) {
                saveStatusSpan.textContent = "Auto-saved " + diffSeconds + " seconds ago";
            } else if (diffSeconds < 3600) {
                const minutes = Math.floor(diffSeconds / 60);
                saveStatusSpan.textContent = "Auto-saved " + minutes + " minutes ago";
            } else {
                const hours = Math.floor(diffSeconds / 3600);
                saveStatusSpan.textContent = "Auto-saved " + hours + " hours ago";
            }
        }
        
        // Find which column is the ID column 
        // 找出哪一列是ID列
        function findIdColumnIndex(headers) {
            // Try to find exact match for "ID" first
            const exactIdIndex = headers.findIndex(header => 
                header.trim().toUpperCase() === "ID");
            
            if (exactIdIndex !== -1) return exactIdIndex;
            
            // If no exact match, look for columns containing "ID"
            const idColumns = headers.map((header, index) => ({
                index,
                header: header.trim().toUpperCase()
            })).filter(item => 
                item.header === "ID" || 
                item.header.includes("ID") || 
                item.header.includes("IDENTIFIER"));
            
            if (idColumns.length > 0) {
                // Sort by preference: exact "ID" first, then shorter names
                idColumns.sort((a, b) => {
                    if (a.header === "ID") return -1;
                    if (b.header === "ID") return 1;
                    return a.header.length - b.header.length;
                });
                return idColumns[0].index;
            }
            
            return -1; // No ID column found
        }
        
        // Function to save data
        // 儲存資料的函數
        function saveData(data) {
            localStorage.setItem(storageKey, JSON.stringify(data));
            lastSaveTime = Math.floor(Date.now() / 1000);
            localStorage.setItem(lastSaveTimeKey, lastSaveTime.toString());
            updateSaveTimeDisplay();
            
            // Show visual feedback for successful save
            // 顯示儲存成功的視覺反饋
            if (saveBtn) {
                saveBtn.textContent = "✓ Saved";
                saveBtn.style.backgroundColor = "#4CAF50";
                setTimeout(function() {
                    saveBtn.textContent = "Save";
                    saveBtn.style.backgroundColor = "";
                }, 1000);
            }
        }
        
        // Import data from Excel file
        // 從Excel檔案匯入資料
        function importExcel(file) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                try {
                    const data = new Uint8Array(e.target.result);
                    const workbook = XLSX.read(data, {type: 'array'});
                    
                    // Get first sheet
                    const firstSheetName = workbook.SheetNames[0];
                    const worksheet = workbook.Sheets[firstSheetName];
                    
                    // Convert to JSON
                    const jsonData = XLSX.utils.sheet_to_json(worksheet, {header: 1});
                    
                    if (jsonData.length < 2) {
                        alert("No data found in Excel file or invalid format");
                        return;
                    }
                    
                    const headers = jsonData[0].map(header => 
                        header ? String(header) : "");
                    
                    // Check if first column header is 'Check'
                    if (headers[0] !== "Check") {
                        alert("Excel file format not recognized. First column should be 'Check'");
                        return;
                    }
                    
                    // Find the ID column index
                    const idColumnIndex = findIdColumnIndex(headers);
                    if (idColumnIndex === -1) {
                        alert("Could not find ID column in Excel file. Please ensure one of the columns is labeled as ID.");
                        return;
                    }
                    
                    console.log("Using column '" + headers[idColumnIndex] + "' as ID column");
                    
                    // Create a map of ID -> Check value
                    const checkValuesByID = {};
                    for (let i = 1; i < jsonData.length; i++) {
                        const row = jsonData[i];
                        if (row.length > idColumnIndex && row[idColumnIndex] !== undefined && row[idColumnIndex] !== null) {
                            const id = String(row[idColumnIndex]).trim(); // Convert to string and trim
                            if (id) {
                                checkValuesByID[id] = row[0] || ""; // Column 0 is the Check column
                            }
                        }
                    }
                    
                    // Find ID column in the HTML table
                    const table = document.querySelector("#tableSelectorDiv table");
                    if (!table) {
                        alert("Table not found in the current page");
                        return;
                    }
                    
                    const tableHeaders = Array.from(table.querySelectorAll("thead th")).map(th => 
                        th.textContent.trim());
                    
                    const tableIdColumnIndex = findIdColumnIndex(tableHeaders);
                    if (tableIdColumnIndex === -1) {
                        alert("Could not find ID column in the table. Please ensure your table has an ID column.");
                        return;
                    }
                    
                    console.log("Using table column '" + tableHeaders[tableIdColumnIndex] + "' as ID column");
                    
                    // Update table with imported values based on ID
                    const rows = table.querySelectorAll("tbody tr");
                    let updatedCount = 0;
                    const updatedData = {}; // For storing the updated data
                    
                    rows.forEach(function(row, index) {
                        // Get the ID from the appropriate column
                        const idCell = row.querySelectorAll("td")[tableIdColumnIndex];
                        if (!idCell) return;
                        
                        const id = idCell.textContent.trim();
                        if (!id) return;
                        
                        // If we have a Check value for this ID
                        if (checkValuesByID[id] !== undefined) {
                            const input = row.querySelector("td:first-child input");
                            if (input) {
                                input.value = checkValuesByID[id];
                                updatedData[index] = checkValuesByID[id];
                                updatedCount++;
                            }
                        }
                    });
                    
                    // Save imported data
                    saveData(updatedData);
                    
                    alert("Successfully imported " + updatedCount + " values from Excel");
                    
                } catch (error) {
                    console.error("Error importing Excel:", error);
                    alert("Error importing Excel file: " + error.message);
                }
            };
            
            reader.onerror = function() {
                alert("Error reading the Excel file");
            };
            
            reader.readAsArrayBuffer(file);
        }
        
        const tableDiv = document.getElementById("tableSelectorDiv");
        if (!tableDiv) {
            console.error("tableSelectorDiv element not found");
            return;
        }
        
        function setupTable() {
            const table = tableDiv.querySelector("table");
            if (!table) {
                console.error("Table element not found");
                return;
            }

            // Insert datalist for dropdown
            // 插入下拉選單的數據列表
            if (!document.getElementById("checkOptions")) {
                const datalist = document.createElement("datalist");
                datalist.id = "checkOptions";
                ["mutation", "tech", "tech_bg", "?mutation", "?tech"].forEach(function(opt) {
                    const option = document.createElement("option");
                    option.value = opt;
                    datalist.appendChild(option);
                });
                document.body.appendChild(datalist);
            }

            // Insert 'Check' column header
            // 插入 'Check' 列標題
            const theadRow = table.querySelector("thead tr");
            if (!theadRow) {
                console.error("Table header row not found");
                return;
            }
            
            // Check if Check column already exists
            // 檢查是否已經存在Check列
            if (!theadRow.querySelector("th:first-child, th") || theadRow.querySelector("th:first-child, th").textContent !== "Check") {
                const checkHeader = document.createElement("th");
                checkHeader.textContent = "Check";
                theadRow.insertBefore(checkHeader, theadRow.firstChild);
            }

            // Restore saved input values
            // 恢復已保存的輸入值
            const storedData = JSON.parse(localStorage.getItem(storageKey) || "{}");

            const rows = table.querySelectorAll("tbody tr");
            rows.forEach(function(row, index) {
                // Check if first cell is already our Check column
                // 檢查行的第一個單元格是否已經是我們的Check欄位
                const firstCell = row.querySelector("td:first-child");
                if (firstCell && firstCell.querySelector("input[list='checkOptions']")) {
                    // Already set up, update value
                    // 已經設置過了，更新值
                    const input = firstCell.querySelector("input");
                    input.value = storedData[index] || "";
                } else {
                    // Create new Check cell
                    // 創建新的Check單元格
                    const td = document.createElement("td");
                    const input = document.createElement("input");
                    input.setAttribute("list", "checkOptions");
                    input.value = storedData[index] || "";
                    input.addEventListener("input", function() {
                        storedData[index] = input.value;
                        saveData(storedData);
                    });
                    td.appendChild(input);
                    row.insertBefore(td, row.firstChild);
                }
            });

            // Create control panel - check if it already exists
            // 建立控制面板 - 先檢查是否已存在
            let controlPanel = tableDiv.querySelector(".check-control-panel");
            if (controlPanel) {
                controlPanel.remove(); // Remove existing panel to avoid duplication
            }
            
            controlPanel = document.createElement("div");
            controlPanel.className = "check-control-panel";
            controlPanel.style = "margin: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9;";
            
            // Display current storage identifier
            // 顯示目前使用的儲存識別符
            const idInfoDiv = document.createElement("div");
            idInfoDiv.style = "margin-bottom: 10px; font-size: 12px; color: #666;";
            idInfoDiv.textContent = "Table Storage ID: " + storageKey;
            
            // Create button container
            // 建立按鈕容器
            const buttonContainer = document.createElement("div");
            buttonContainer.style = "display: flex; gap: 10px; margin-bottom: 10px;";
            
            // Manual save button
            // 手動儲存按鈕
            saveBtn = document.createElement("button");
            saveBtn.textContent = "Save";
            saveBtn.style = "padding: 5px 10px; cursor: pointer;";
            saveBtn.addEventListener("click", function() {
                // Get current data and save
                // 獲取當前資料並儲存
                const currentData = {};
                table.querySelectorAll("tbody tr").forEach(function(row, idx) {
                    const input = row.querySelector("td:first-child input");
                    if (input) {
                        currentData[idx] = input.value;
                    }
                });
                saveData(currentData);
            });
            
            // Export to Excel button
            const exportBtn = document.createElement("button");
            exportBtn.textContent = "Export Excel";
            exportBtn.style = "padding: 5px 10px; cursor: pointer;";
            exportBtn.addEventListener("click", function() {
                const headers = Array.from(table.querySelectorAll("thead th")).map(function(th) {
                    return th.textContent;
                });
                const data = [headers];

                table.querySelectorAll("tbody tr").forEach(function(row) {
                    const tds = Array.from(row.querySelectorAll("td"));
                    const rowData = tds.map(function(td, i) {
                        if (i === 0) {
                            const input = td.querySelector("input");
                            return input ? input.value : "";
                        }
                        return td.textContent;
                    });
                    data.push(rowData);
                });

                const ws = XLSX.utils.aoa_to_sheet(data);
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, "Variants");
                XLSX.writeFile(wb, "variant_check_result.xlsx");
            });
            
            // Import from Excel button and file input
            // 從Excel匯入的按鈕和檔案輸入
            const importContainer = document.createElement("div");
            importContainer.style = "position: relative; display: inline-block;";
            
            const importBtn = document.createElement("button");
            importBtn.textContent = "Import Excel";
            importBtn.style = "padding: 5px 10px; cursor: pointer;";
            
            const fileInput = document.createElement("input");
            fileInput.type = "file";
            fileInput.accept = ".xlsx, .xls";
            fileInput.style = "position: absolute; top: 0; left: 0; opacity: 0; width: 100%; height: 100%; cursor: pointer;";
            
            fileInput.addEventListener("change", function(e) {
                if (this.files && this.files.length > 0) {
                    importExcel(this.files[0]);
                    this.value = ''; // Reset file input for future imports
                }
            });
            
            importContainer.appendChild(importBtn);
            importContainer.appendChild(fileInput);

            // Clear saved data button
            // 清除儲存資料的按鈕
            const clearBtn = document.createElement("button");
            clearBtn.textContent = "Clear Data";
            clearBtn.style = "padding: 5px 10px; cursor: pointer;";
            clearBtn.addEventListener("click", function() {
                localStorage.removeItem(storageKey);
                localStorage.removeItem(lastSaveTimeKey);
                lastSaveTime = 0;
                updateSaveTimeDisplay();
                alert("Data cleared. Please refresh the page to apply changes.");
            });
            
            // Add buttons to container
            // 添加按鈕到容器
            buttonContainer.appendChild(saveBtn);
            buttonContainer.appendChild(exportBtn);
            buttonContainer.appendChild(importContainer);
            buttonContainer.appendChild(clearBtn);
            
            // Status display for last save time
            // 顯示最後儲存時間的狀態列
            const statusContainer = document.createElement("div");
            statusContainer.style = "font-size: 12px; color: #666; display: flex; align-items: center;";
            
            const saveStatusLabel = document.createElement("span");
            saveStatusLabel.textContent = "Status: ";
            saveStatusLabel.style = "margin-right: 5px;";
            
            saveStatusSpan = document.createElement("span");
            saveStatusSpan.style = "font-weight: bold;";
            
            statusContainer.appendChild(saveStatusLabel);
            statusContainer.appendChild(saveStatusSpan);
            
            // Add all elements to control panel
            // 將所有元素添加到控制面板
            controlPanel.appendChild(idInfoDiv);
            controlPanel.appendChild(buttonContainer);
            controlPanel.appendChild(statusContainer);
            
            // Add control panel to table
            // 將控制面板添加到表格前
            tableDiv.insertBefore(controlPanel, tableDiv.firstChild);
            
            // Initialize save time display
            // 初始化儲存時間顯示
            updateSaveTimeDisplay();
        }
        
        // Update save time display every 10 seconds
        // 每10秒更新一次儲存時間顯示
        setInterval(updateSaveTimeDisplay, 10000);
        
        // If table already exists, set up immediately
        // 如果表格已經存在，直接設置
        const existingTable = tableDiv.querySelector("table");
        if (existingTable) {
            setupTable();
        } else {
            // Use MutationObserver to wait for table to appear
            // 使用MutationObserver等待表格出現
            const observer = new MutationObserver(function(mutations) {
                for (const mutation of mutations) {
                    if (mutation.type === 'childList' && tableDiv.querySelector("table")) {
                        setupTable();
                        observer.disconnect();
                        break;
                    }
                }
            });
            
            observer.observe(tableDiv, { childList: true, subtree: true });
        }
    });
    </script>
    """
    return script

def inject_check_column_features(input_file: str, output_file: str):
    """Inject Check column, autosave and export functionality into HTML file.
    將Check欄位、自動儲存和匯出功能注入HTML檔案。"""
    # Generate unique identifier (filename_contenthash_timestamp)
    # 生成唯一識別符 (檔案名_內容雜湊_時間戳)
    unique_id = generate_unique_id(input_file)
    
    with open(input_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    script = generate_script_js(unique_id)
    soup.body.append(BeautifulSoup(script, "html.parser"))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(str(soup))
    
    print(f"Successfully processed file: {output_file}")
    print(f"Storage identifier used: check_column_autosave_{unique_id}")

def main():
    parser = argparse.ArgumentParser(
        description="Inject a 'Check' column with dropdown, autosave, and export to Excel functionality into an HTML table."
    )
    parser.add_argument("-i", "--input", required=True, help="Input HTML file path")
    parser.add_argument("-o", "--output", required=True, help="Output HTML file path")

    args = parser.parse_args()
    inject_check_column_features(args.input, args.output)

if __name__ == "__main__":
    main()