document.addEventListener("DOMContentLoaded", () => {
    const historyEntries = document.querySelectorAll(".history-entry");
    const deleteButtons = document.querySelectorAll(".delete-button");
    const deleteAllButton = document.getElementById("deleteAllButton");
    const historyContainer = document.querySelector(".history-container");
    const modal = document.getElementById("modal");
    const modalProbs = document.getElementById("modalProbs");
    const modalTimestamp = document.getElementById("modalTimestamp");
    const deleteAllModal = document.getElementById("deleteAllModal"); 
    const confirmDeleteButton = document.getElementById("confirmDelete");
    const cancelDeleteButton = document.getElementById("cancelDelete");
    const closeModal = document.getElementById("closeModal");
    const deleteAllUrl = deleteAllButton.dataset.deleteAllUrl;
    const deleteSingleUrl = deleteAllButton.dataset.deleteSingleUrl;
    const TIMEOUT_DURATION = 1 * 60 * 1000;
    let timeout;

    function createCollapsibleSection(title, contentList) {
        const section = document.createElement("div");
        section.classList.add("collapsible-section");

        const header = document.createElement("strong");
        header.classList.add("collapsible-header");
        header.textContent = title;
        header.addEventListener("click", () => {
            content.classList.toggle("visible");
        });

        const content = document.createElement("div");
        content.classList.add("collapsible-content");

        contentList.forEach(item => {
            const paragraph = document.createElement("p");
            paragraph.textContent = item;
            content.appendChild(paragraph);
        });

        section.appendChild(header);
        section.appendChild(content);
        return section;
    }

    function deleteAllHistory() {
        fetch(deleteAllUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ delete_all: true }),
        }).then(response => {
            if (response.ok) {
                historyContainer.innerHTML = `
                <label class="history-nothing">
                    <img src="/static/photo/履歴ない.png" alt="履歴ないwow">
                </label>
                `;
            } else {
                console.error("一括削除に失敗しました。");
            }
        }).catch(error => console.error("エラー:", error));
    }

    if (deleteAllButton) {
        deleteAllButton.addEventListener("click", () => {
            deleteAllModal.classList.add("show");
        });
    }

    confirmDeleteButton.addEventListener("click", () => {
        deleteAllHistory();
        deleteAllModal.classList.remove("show");
    });

    cancelDeleteButton.addEventListener("click", () => {
        deleteAllModal.classList.remove("show");
    });

    deleteButtons.forEach(button => {
        button.addEventListener('click', function (event) {
            event.stopPropagation();
            const imageId = this.dataset.imageId;
            fetch(deleteSingleUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_id: imageId }),
            }).then(response => {
                if (response.ok) {
                    const entryToDelete = document.querySelector(`[data-image-id="${imageId}"]`);
                    if (entryToDelete) entryToDelete.closest(".history-entry").remove();
                } else {
                    console.error('削除に失敗しました。');
                }
            }).catch(error => console.error('エラー:', error));
        });
    });

    closeModal.addEventListener("click", () => modal.classList.remove("show"));
    modal.addEventListener("click", (event) => {
        if (event.target === modal) modal.classList.remove("show");
    });

    historyEntries.forEach(entry => {
        entry.addEventListener("click", () => {
            const dataProbs = JSON.parse(entry.dataset.probs);
            const labels = JSON.parse(entry.dataset.labels);
            const emotions = entry.dataset.emotions ? JSON.parse(entry.dataset.emotions) : {};
            const labelOrder = {
                'ネコ-怒る': 0, 'ネコ-楽しい': 1, 'ネコ-悲しい': 2,
                'イヌ-怒る': 3, 'イヌ-楽しい': 4, 'イヌ-悲しい': 5,
                'ライオン-怒る': 6, 'ライオン-楽しい': 7, 'ライオン-悲しい': 8,
                'サル-怒る': 9, 'サル-楽しい': 10, 'サル-悲しい': 11,
                'オオカミ-怒る': 12, 'オオカミ-楽しい': 13, 'オオカミ-悲しい': 14
            };
            const initialProbs = dataProbs.map((prob, index) => ({ label: labels[index], prob }));
            const initialEmotions = Object.keys(labelOrder).map(label => ({
                label,
                prob: emotions[label] !== undefined ? emotions[label] : 0
            }));

            let isSortedByLabel = false;
            let sortedProbs = [...initialProbs].sort((a, b) => b.prob - a.prob);
            let sortedEmotions = [...initialEmotions].sort((a, b) => b.prob - a.prob);
            function displayProbs(probs, emotions) {
                modalProbs.innerHTML = "";
                const roundedProbs = probs.map(item => `${item.label}: ${item.prob.toFixed(1)}%`);
                modalProbs.appendChild(createCollapsibleSection("確率", roundedProbs));
                const roundedEmotions = emotions.map(item => `${item.label}: ${item.prob.toFixed(1)}%`);
                modalProbs.appendChild(createCollapsibleSection("感情確率", roundedEmotions.length ? roundedEmotions : ["データなし"]));
            }

            displayProbs(sortedProbs, sortedEmotions);

            const timestamp = entry.dataset.timestamp;
            const date = new Date(timestamp);
            modalTimestamp.textContent = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
            modal.classList.add("show");

            const sortByLabelButton = document.getElementById("sortByLabelButton");
            sortByLabelButton.textContent = "ラベル順に並べ替え";
            sortByLabelButton.onclick = () => {
                if (isSortedByLabel) {
                    sortedProbs = [...initialProbs].sort((a, b) => b.prob - a.prob);
                    sortedEmotions = [...initialEmotions].sort((a, b) => b.prob - a.prob);
                    sortByLabelButton.textContent = "ラベル順に並べ替え";
                } else {
                    sortedProbs = [...initialProbs].sort((a, b) => labelOrder[a.label] - labelOrder[b.label]);
                    sortedEmotions = [...initialEmotions].sort((a, b) => labelOrder[a.label] - labelOrder[b.label]);
                    sortByLabelButton.textContent = "確率順に並べ替え";
                }
                isSortedByLabel = !isSortedByLabel;
                displayProbs(sortedProbs, sortedEmotions);
            };
        });
    });

    function resetTimeout() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            if (!modal.classList.contains("show")) window.location.href = TIMEOUT_URL;
        }, TIMEOUT_DURATION);
    }

    document.addEventListener("mousemove", resetTimeout);
    document.addEventListener("keypress", resetTimeout);
    document.addEventListener("click", resetTimeout);
    document.addEventListener("scroll", resetTimeout);
    resetTimeout();
});
