// AI Website Audit Agent Suite - Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const auditForm = document.getElementById('auditForm');
    const submitBtn = document.getElementById('submitBtn');
    const loadingState = document.getElementById('loadingState');
    const resultsSection = document.getElementById('resultsSection');
    const errorState = document.getElementById('errorState');

    auditForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await runAudit();
    });
});

async function runAudit() {
    const websiteUrl = document.getElementById('websiteUrl').value;
    const industry = document.getElementById('industry').value;
    const monthlyVisitors = document.getElementById('monthlyVisitors').value;
    const averageClientValue = document.getElementById('averageClientValue').value;
    const creatorProfile = document.getElementById('creatorProfile').value;
    const email = document.getElementById('email').value;

    if (!websiteUrl || !industry) {
        showError('Please fill in all required fields.');
        return;
    }

    showLoadingState();

    try {
        console.log('1. Starting audit process...');
        const response = await fetch('/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                website_url: websiteUrl,
                industry: industry,
                monthly_visitors: monthlyVisitors ? parseInt(monthlyVisitors) : null,
                average_client_value: averageClientValue ? parseFloat(averageClientValue) : null,
                creator_profile: creatorProfile || null,
                email: email || null
            }),
        });

        console.log('2. Received response from server:', response.status, response.statusText);

        if (!response.ok) {
            let errorDetail = 'Unknown server error';
            try {
                const errorData = await response.json();
                errorDetail = errorData.detail || JSON.stringify(errorData);
            } catch (e) {
                errorDetail = await response.text();
            }
            throw new Error(errorDetail);
        }

        // Get raw text to debug JSON issues
        const responseText = await response.text();
        console.log('3. Raw response text:', responseText);

        let results;
        try {
            results = JSON.parse(responseText);
            console.log('4. Successfully parsed JSON.');
        } catch (e) {
            console.error('JSON parsing failed:', e);
            throw new Error('Failed to parse server response. See console for details.');
        }

        console.log('5. Calling displayResults...');
        displayResults(results);

    } catch (error) {
        console.error('Audit failed:', error);
        showError(error.message);
    }
}

function showLoadingState() {
    document.getElementById('auditForm').parentElement.style.display = 'none';
    document.getElementById('loadingState').classList.remove('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('errorState').classList.add('hidden');

    // Simulate progress updates
    setTimeout(() => {
        updateLoadingProgress(0);
    }, 1000);
    
    setTimeout(() => {
        updateLoadingProgress(1);
    }, 3000);
    
    setTimeout(() => {
        updateLoadingProgress(2);
    }, 5000);
}

function updateLoadingProgress(step) {
    const steps = document.querySelectorAll('#loadingState .flex.items-center');
    
    steps.forEach((stepEl, index) => {
        const icon = stepEl.querySelector('i');
        if (index < step) {
            icon.className = 'fas fa-check-circle text-green-500 mr-2';
        } else if (index === step) {
            icon.className = 'fas fa-spinner fa-spin text-blue-500 mr-2';
        } else {
            icon.className = 'fas fa-clock mr-2';
        }
    });
}

function displayResults(results) {
    console.log('Raw results received in displayResults:', results);
    
    // The backend now returns data in the format: {status: 'success', audit_id: '...', data: {...}}
    if (!results || !results.data) {
        console.error("Invalid response format:", results);
        showError("Received an invalid response from the server.");
        return;
    }
    
    const auditData = results.data;
    console.log('Audit data extracted:', auditData);

    // Hide loading state and show results
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('resultsSection').classList.remove('hidden');

    try {
        // Calculate overall score as average of all category scores
        const scores = auditData.scores;
        const scoreValues = Object.values(scores || {});
        const overallScore = scoreValues.length > 0 
            ? Math.round(scoreValues.reduce((a, b) => a + b, 0) / scoreValues.length)
            : 0;
            
        console.log('Calculated overall score:', overallScore);
        
        // Display overall score
        displayOverallScore(overallScore, 'Your comprehensive audit is complete.');

        // Display category scores
        if (auditData.scores) {
            displayCategoryScores(auditData.scores);
        }

        // Display critical issues
        if (auditData.critical_issues) {
            displayCriticalIssues(auditData.critical_issues);
        }

        // Display quick wins
        if (auditData.quick_wins) {
            displayQuickWins(auditData.quick_wins);
        }

        // Display recommendations
        if (auditData.recommendations) {
            displayRecommendations(auditData.recommendations);
        }

        // Populate detailed report
        populateDetailedReport(auditData);

        // Display next steps
        if (auditData.next_steps) {
            // This part can be implemented if a next_steps section is added to HTML
        }

    } catch (error) {
        console.error('Error rendering results:', error);
        showError('Failed to display audit results. Please check the console.');
    }
}

function displayOverallScore(score, summary) {
    console.log(`Attempting to display overall score: ${score}`);
    const scoreElement = document.getElementById('scoreValue');
    const summaryElement = document.getElementById('scoreSummary');
    const scoreCircle = document.getElementById('scoreCircleContainer');

    console.log({ scoreElement, summaryElement, scoreCircle });

    if (scoreElement) {
        scoreElement.textContent = score;
    }
    if (summaryElement) {
        summaryElement.textContent = summary;
    }

    // Update score circle color based on score
    if (scoreCircle) {
        scoreCircle.className = 'mx-auto w-32 h-32 rounded-full flex items-center justify-center mb-4 ' + getScoreClass(score);
    } else {
        console.error("'scoreCircleContainer' not found!");
    }
}

function getScoreClass(score) {
    if (score >= 80) return 'score-excellent';
    if (score >= 60) return 'score-good';
    if (score >= 40) return 'score-fair';
    return 'score-poor';
}

function displayCategoryScores(categoryScores) {
    const container = document.getElementById('categoryScores');
    container.innerHTML = '';

    // Default categories that match the backend structure
    const categories = [
        { 
            key: 'conversion_readiness', 
            name: 'Conversion Readiness', 
            icon: 'fas fa-check-circle',
            description: 'Evaluates how well the website is optimized for conversions',
            impact: 'High'
        },
        { 
            key: 'trust_signals', 
            name: 'Trust Signals', 
            icon: 'fas fa-shield-alt',
            description: 'Assesses elements that build trust with visitors',
            impact: 'High'
        },
        { 
            key: 'user_experience', 
            name: 'User Experience', 
            icon: 'fas fa-user-check',
            description: 'Reviews overall usability and user journey',
            impact: 'High'
        },
        { 
            key: 'content_quality', 
            name: 'Content Quality', 
            icon: 'fas fa-file-alt',
            description: 'Evaluates content effectiveness and engagement',
            impact: 'Medium'
        },
        { 
            key: 'seo_foundations', 
            name: 'SEO Foundations', 
            icon: 'fas fa-search',
            description: 'Checks basic search engine optimization elements',
            impact: 'High'
        },
        { 
            key: 'performance_metrics', 
            name: 'Performance', 
            icon: 'fas fa-tachometer-alt',
            description: 'Measures site speed and performance metrics',
            impact: 'Medium'
        }
    ];

    // If no scores are provided, show a message
    if (!categoryScores || Object.keys(categoryScores).length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-8">
                <i class="fas fa-info-circle text-4xl text-blue-500 mb-4"></i>
                <h3 class="text-xl font-semibold text-gray-800 mb-2">No Category Scores Available</h3>
                <p class="text-gray-600">The audit did not return specific category scores. Please check the key findings and recommendations for detailed feedback.</p>
            </div>
        `;
        return;
    }

    // Calculate overall score
    let totalScore = 0;
    let validCategories = 0;
    
    // First pass: Calculate total score
    for (const category of categories) {
        const score = categoryScores[category.key];
        if (typeof score === 'number' && score > 0) {
            totalScore += score;
            validCategories++;
        }
    }
    
    // If no valid scores, show a message
    if (validCategories === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-8">
                <i class="fas fa-exclamation-triangle text-4xl text-yellow-500 mb-4"></i>
                <h3 class="text-xl font-semibold text-gray-800 mb-2">Incomplete Audit Data</h3>
                <p class="text-gray-600">The audit did not return complete scoring data. Some categories may be missing or invalid.</p>
            </div>
        `;
        return;
    }
    
    const overallScore = Math.round(totalScore / validCategories);
    

    // Second pass: Create cards for each category with valid data
    categories.forEach(category => {
        const scoreData = categoryScores[category.key];
        if (scoreData === undefined || scoreData === null) return;
        
        const score = typeof scoreData === 'number' ? scoreData : (scoreData.score || 0);
        if (score <= 0) return; // Skip categories with invalid scores
        
        const details = Object.assign(
            { 'Impact': category.impact },
            typeof scoreData === 'object' ? scoreData.details || {} : {}
        );
        
        // Add key findings if available
        if (scoreData.key_findings && Array.isArray(scoreData.key_findings) && scoreData.key_findings.length > 0) {
            details['Key Findings'] = scoreData.key_findings[0];
        }
        
        const card = createCategoryCard(
            category.name, 
            category.icon, 
            score, 
            category.description,
            details
        );
        container.appendChild(card);
    });
}

function createCategoryCard(name, icon, score, description, details = {}) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-md overflow-hidden card-hover';
    
    // Create details HTML if available
    let detailsHtml = '';
    if (Object.keys(details).length > 0) {
        detailsHtml = `
            <div class="mt-4 pt-4 border-t border-gray-100">
                ${Object.entries(details).map(([key, value]) => {
                    if (!value) return '';
                    return `
                        <div class="text-left mb-2">
                            <div class="text-sm font-medium text-gray-600 capitalize">${key.replace(/_/g, ' ')}</div>
                            <div class="text-sm text-gray-700">${value}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }
    
    card.innerHTML = `
        <div class="p-6">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center">
                    <div class="text-2xl ${getScoreColor(score)} mr-3">
                        <i class="${icon}"></i>
                    </div>
                    <h4 class="text-lg font-semibold text-gray-800">${name}</h4>
                </div>
                <div class="text-xl font-bold ${getScoreColor(score)}">${Math.round(score)}</div>
            </div>
            
            <div class="w-full bg-gray-200 rounded-full h-2 mb-3">
                <div class="h-2 rounded-full ${getScoreGradient(score)}" style="width: ${score}%"></div>
            </div>
            
            <p class="text-sm text-gray-600 text-left mb-3">${description}</p>
            
            ${detailsHtml}
        </div>
    `;
    
    return card;
}

function getScoreColor(score) {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-blue-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
}

function getScoreGradient(score) {
    if (score >= 80) return 'from-green-500 to-green-600';
    if (score >= 60) return 'from-blue-500 to-blue-600';
    if (score >= 40) return 'from-yellow-500 to-yellow-600';
    return 'from-red-500 to-red-600';
}

function displayCriticalIssues(issues, title = 'Key Findings') {
    const container = document.getElementById('criticalIssues') || document.getElementById('resultsSection');
    
    // Create section header
    const section = document.createElement('div');
    section.className = 'mb-8';
    
    if (!issues || issues.length === 0) {
        section.innerHTML = `
            <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-center mb-4">
                <i class="fas fa-check-circle text-green-500 text-2xl mb-2"></i>
                <p class="text-green-700">No ${title.toLowerCase()} found! Your website is in good shape.</p>
            </div>
        `;
        container.appendChild(section);
        return;
    }
    
    section.innerHTML = `
        <div class="flex items-center mb-4">
            <h2 class="text-xl font-semibold text-gray-800">${title}</h2>
            <span class="ml-2 bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                ${issues.length} ${issues.length === 1 ? 'item' : 'items'}
            </span>
        </div>
    `;
    
    const issuesContainer = document.createElement('div');
    issuesContainer.className = 'space-y-4';
    
    // Process each issue
    issues.forEach((issue, index) => {
        const issueCard = document.createElement('div');
        issueCard.className = 'bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden';
        
        // Handle different issue formats (string or object)
        const issueTitle = typeof issue === 'string' ? issue : (issue.title || `Issue #${index + 1}`);
        const issueDescription = typeof issue === 'string' ? null : (issue.description || '');
        const issueCategory = issue.category || 'General';
        const issuePriority = issue.priority || 'medium';
        
        // Priority styling
        const priorityColors = {
            high: 'bg-red-100 text-red-800',
            medium: 'bg-yellow-100 text-yellow-800',
            low: 'bg-blue-100 text-blue-800'
        };
        
        issueCard.innerHTML = `
            <div class="p-4">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <h3 class="text-base font-medium text-gray-900">${issueTitle}</h3>
                        ${issueDescription ? `<p class="mt-1 text-sm text-gray-600">${issueDescription}</p>` : ''}
                    </div>
                    <span class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${priorityColors[issuePriority.toLowerCase()] || 'bg-gray-100 text-gray-800'}">
                        ${issuePriority}
                    </span>
                </div>
                <div class="mt-2 flex items-center text-xs text-gray-500">
                    <span>${issueCategory}</span>
                </div>
            </div>
        `;
        
        issuesContainer.appendChild(issueCard);
    });
    
    section.appendChild(issuesContainer);
    container.appendChild(section);
    
}

// Add these helper functions at the bottom of the file
function toggleAccordion(id) {
    const content = document.getElementById(`content-${id}`);
    const icon = document.getElementById(`icon-${id}`);
    
    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        icon.classList.add('rotate-180');
    } else {
        content.classList.add('hidden');
        icon.classList.remove('rotate-180');
    }
}

function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

function displayQuickWins(wins) {
    const container = document.getElementById('quickWins');
    container.innerHTML = '';

    if (!wins || wins.length === 0) {
        container.innerHTML = `
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
                <i class="fas fa-info-circle text-yellow-500 text-2xl mb-2"></i>
                <p class="text-yellow-700">No quick wins identified. All optimizations may require more significant changes.</p>
            </div>
        `;
        return;
    }

    // Create a grid layout for quick wins
    const grid = document.createElement('div');
    grid.className = 'grid grid-cols-1 md:grid-cols-2 gap-4';
    
    wins.forEach((win, index) => {
        const winText = typeof win === 'string' ? win : win.title || win.description || `Quick Win #${index + 1}`;
        const winDescription = (typeof win === 'object' && win.description) ? win.description : '';
        
        const card = document.createElement('div');
        card.className = 'bg-white rounded-lg shadow-sm p-4 border border-gray-100 hover:border-yellow-300 transition-colors';
        card.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0 h-6 w-6 rounded-full bg-yellow-100 flex items-center justify-center mr-3 mt-0.5">
                    <i class="fas fa-bolt text-yellow-500 text-xs"></i>
                </div>
                <div>
                    <h4 class="text-sm font-medium text-gray-900">${winText}</h4>
                    ${winDescription ? `<p class="mt-1 text-sm text-gray-500">${winDescription}</p>` : ''}
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
    
    container.appendChild(grid);
}

function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendations');
    if (!container) return;
    container.innerHTML = '';

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = `
            <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                <i class="fas fa-check-circle text-green-500 text-2xl mb-2"></i>
                <p class="text-green-700">No specific recommendations were generated. Your website is performing well in the audited areas.</p>
            </div>
        `;
        return;
    }

    const accordion = document.createElement('div');
    accordion.className = 'space-y-2';

    recommendations.forEach((rec, index) => {
        const recTitle = rec.title || `Recommendation #${index + 1}`;
        const recDescription = rec.description || '';
        const recCategory = rec.category || 'General';
        const recPriority = rec.priority || 'medium';

        const priorityColors = {
            high: 'border-red-500',
            medium: 'border-yellow-500',
            low: 'border-blue-500'
        };

        const item = document.createElement('div');
        item.className = `bg-white rounded-lg shadow-sm border-l-4 ${priorityColors[recPriority.toLowerCase()] || 'border-gray-300'}`;
        item.innerHTML = `
            <button onclick="toggleAccordion('rec-${index}')" class="w-full text-left p-4 focus:outline-none">
                <div class="flex items-center justify-between">
                    <h4 class="text-md font-semibold text-gray-800">${recTitle}</h4>
                    <i id="icon-rec-${index}" class="fas fa-chevron-down transform transition-transform"></i>
                </div>
            </button>
            <div id="content-rec-${index}" class="hidden px-4 pb-4">
                <p class="text-sm text-gray-600">${recDescription}</p>
                <div class="mt-3 flex items-center justify-between text-xs text-gray-500">
                    <span>Category: ${recCategory}</span>
                    <span class="capitalize">Priority: ${recPriority}</span>
                </div>
            </div>
        `;
        accordion.appendChild(item);
    });

    container.appendChild(accordion);


    // Group recommendations by category if they have one
    const recommendationsByCategory = {};

    recommendations.forEach(rec => {
        const category = (rec && rec.category) ? rec.category : 'General';
        if (!recommendationsByCategory[category]) {
            recommendationsByCategory[category] = [];
        }
        recommendationsByCategory[category].push(rec);
    });

    // Create a section for each category
    Object.entries(recommendationsByCategory).forEach(([category, recs]) => {
        const categorySection = document.createElement('div');
        categorySection.className = 'mb-8';

        categorySection.innerHTML = `
            <h3 class="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                <i class="fas fa-folder-open text-blue-500 mr-2"></i>
                ${category}
                <span class="ml-2 bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                    ${recs.length} ${recs.length === 1 ? 'item' : 'items'}
                </span>
            </h3>
        `;

        const recsContainer = document.createElement('div');
        recsContainer.className = 'space-y-4';

        recs.forEach((rec, index) => {
            const recItem = document.createElement('div');
            recItem.className = 'bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden';

            const title = (typeof rec === 'string') ? rec : (rec.title || `Recommendation #${index + 1}`);
            const description = (typeof rec === 'string') ? '' : (rec.description || rec.details || '');
            const priority = (rec && rec.priority) ? rec.priority : 'medium';
            const impact = (rec && rec.impact) ? rec.impact : 'medium';

            const priorityColors = {
                high: 'bg-red-100 text-red-800',
                medium: 'bg-yellow-100 text-yellow-800',
                low: 'bg-blue-100 text-blue-800'
            };

            const impactIcons = {
                high: 'fas fa-arrow-up text-red-500',
                medium: 'fas fa-arrow-right text-yellow-500',
                low: 'fas fa-arrow-down text-blue-500'
            };

            recItem.innerHTML = `
                <div class="p-4">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <h4 class="font-medium text-gray-900">${title}</h4>
                            ${description ? `<p class="mt-1 text-sm text-gray-600">${description}</p>` : ''}
                        </div>
                        <div class="flex flex-col items-end ml-4">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mb-1 ${priorityColors[priority.toLowerCase()] || 'bg-gray-100 text-gray-800'}">
                                <i class="fas fa-flag mr-1"></i> ${priority}
                            </span>
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${priorityColors[impact.toLowerCase()] || 'bg-gray-100 text-gray-800'}">
                                <i class="${impactIcons[impact.toLowerCase()] || 'fas fa-arrows-alt-h'} mr-1"></i> ${impact} Impact
                            </span>
                        </div>
                    </div>
                    ${(rec && rec.steps) ? `
                        <div class="mt-3 pt-3 border-t border-gray-100">
                            <h5 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Implementation Steps</h5>
                            <ol class="list-decimal list-inside space-y-1 text-sm text-gray-700">
                                ${Array.isArray(rec.steps) ? 
                                    rec.steps.map(step => `<li>${step}</li>`).join('') : 
                                    `<li>${rec.steps}</li>`
                                }
                            </ol>
                        </div>
                    ` : ''}
                </div>
            `;

            recsContainer.appendChild(recItem);
        });

        categorySection.appendChild(recsContainer);
        container.appendChild(categorySection);
    });
}

function populateDetailedReport(auditData) {
    try {
        // Helper function to create list items from an array
        const createListItems = (items) => {
            if (!items || !Array.isArray(items)) return '';
            return items.map(item => `<li>${item}</li>`).join('');
        };

        // Helper function to get impact class
        const getImpactClass = (impact) => {
            const impactMap = {
                'high': 'bg-red-100 text-red-800',
                'medium': 'bg-yellow-100 text-yellow-800',
                'low': 'bg-green-100 text-green-800'
            };
            return impactMap[impact?.toLowerCase()] || 'bg-gray-100 text-gray-800';
        };

        // Process each category in the scores
        if (auditData.scores) {
            Object.entries(auditData.scores).forEach(([category, score]) => {
                const categoryData = auditData[category];
                if (!categoryData) return;

                const sectionId = `${category.replace(/\s+/g, '-').toLowerCase()}`;
                let section = document.getElementById(sectionId);
                
                // If section doesn't exist, create it
                if (!section) {
                    const container = document.getElementById('report-sections');
                    if (!container) return;
                    
                    const newSection = document.createElement('div');
                    newSection.id = sectionId;
                    newSection.className = 'mb-8';
                    newSection.innerHTML = `
                        <h3 class="text-xl font-semibold text-gray-700 mb-4">${formatCategoryName(category)}</h3>
                        <div class="bg-gray-50 p-6 rounded-lg">
                            <div class="flex justify-between items-center mb-4">
                                <h4 class="font-medium text-gray-700">Score: <span class="font-bold">${score}/100</span></h4>
                                <span class="px-3 py-1 rounded-full text-sm font-medium ${getImpactClass(categoryData.impact_assessment)}">
                                    ${categoryData.impact_assessment || 'N/A'}
                                </span>
                            </div>
                            <div class="space-y-6">
                                <div>
                                    <h5 class="font-medium text-gray-700 mb-2">Key Findings</h5>
                                    <ul class="list-disc pl-5 space-y-1 text-gray-600">
                                        ${createListItems(categoryData.key_findings)}
                                    </ul>
                                </div>
                                <div>
                                    <h5 class="font-medium text-gray-700 mb-2">Recommendations</h5>
                                    <ul class="list-disc pl-5 space-y-1 text-gray-600">
                                        ${createListItems(categoryData.recommendations)}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    `;
                    container.appendChild(newSection);
                } else {
                    // Update existing section
                    const scoreEl = section.querySelector('.score-value');
                    const impactEl = section.querySelector('.impact-badge');
                    const findingsEl = section.querySelector('.findings-list');
                    const recommendationsEl = section.querySelector('.recommendations-list');
                    
                    if (scoreEl) scoreEl.textContent = `${score}/100`;
                    if (impactEl) {
                        impactEl.className = `px-3 py-1 rounded-full text-sm font-medium ${getImpactClass(categoryData.impact_assessment)}`;
                        impactEl.textContent = categoryData.impact_assessment || 'N/A';
                    }
                    if (findingsEl) findingsEl.innerHTML = createListItems(categoryData.key_findings);
                    if (recommendationsEl) recommendationsEl.innerHTML = createListItems(categoryData.recommendations);
                }
            });
        }
    } catch (error) {
        console.error('Error populating detailed report:', error);
    }
}

// Helper function to format category names
function formatCategoryName(category) {
    return category
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function showError(message) {
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('errorState').classList.remove('hidden');
    document.getElementById('errorMessage').textContent = message;
}

function resetForm() {
    document.getElementById('auditForm').parentElement.style.display = 'block';
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('errorState').classList.add('hidden');
    
    // Clear form
    document.getElementById('auditForm').reset();
}
