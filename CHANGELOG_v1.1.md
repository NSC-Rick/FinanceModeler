# Financial Modeler Version 1.1 - Release Notes

## Release Date: January 2026

## Overview
Version 1.1 focuses on usability and readability improvements without changing any underlying financial calculations or business logic. All enhancements maintain backward compatibility with existing saved models.

---

## ✨ New Features & Enhancements

### Enhancement 1: Default Expense Amount Changed to $0

**What Changed:**
- When adding a new Operating Expense, the default amount is now **$0.00** (previously $1,000.00)

**Why This Matters:**
- Users now intentionally enter expense values rather than having to overwrite a placeholder
- Reduces errors from forgetting to update default values
- Cleaner data entry experience

**Files Modified:**
- `ui/opex_page.py` (line 101)

**Backward Compatibility:**
- ✅ Existing saved models are unaffected
- ✅ No calculation changes

---

### Enhancement 2: Projection Start Month/Year Settings

**What Changed:**
- Added new settings to define the beginning of your projection timeline
- Calendar-based labels now replace generic "Period 1, Period 2, Period 3" throughout the application

**New UI Controls (Home Page):**
- **Projection Start Month** dropdown (January - December)
- **Projection Start Year** dropdown (current year ± 2-6 years)

**Where Labels Appear:**
- ✅ Income Statement columns
- ✅ Cash Flow Statement columns
- ✅ Loan Amortization Schedule columns
- ✅ Key Performance Indicators columns
- ✅ All charts (Revenue, Cash Flow, DSCR)
- ✅ Excel exports

**Examples:**

| Old Label | New Label (Jan 2026 start) |
|-----------|----------------------------|
| Period 1  | Jan 2026                   |
| Period 2  | Feb 2026                   |
| Period 12 | Dec 2026                   |
| Period 13 | Jan 2027                   |

**Annual Mode:**
| Old Label | New Label (2026 start) |
|-----------|------------------------|
| Period 1  | 2026                   |
| Period 2  | 2027                   |
| Period 3  | 2028                   |

**Files Modified:**
- `ui/home.py` - Added start month/year settings and UI controls
- `ui/review_page.py` - Applied calendar labels to all statements and charts
- `utils/period_labels.py` - New utility module for label generation
- `requirements.txt` - Added python-dateutil dependency

**Technical Details:**
- Internal period numbering (0, 1, 2, ...) remains unchanged for calculations
- Only presentation labels are modified
- Month labels correctly roll across years (Dec → Jan)
- Fully compatible with both Monthly and Annual time modes

**Backward Compatibility:**
- ✅ Existing models default to January of current year
- ✅ All calculations remain identical
- ✅ Users can adjust start date at any time

---

### Enhancement 3: Improved Guidance Text Contrast

**What Changed:**
- All instructional/help text displayed on blue information panels now uses **white (#FFFFFF)** text
- Significantly improved readability of guidance text throughout the application

**Where Applied:**
- All `st.info()` panels across every page
- Revenue guidance
- COGS guidance
- Seasonality information
- Startup ramp explanations
- Cash flow mode indicators
- Working capital explanations
- And all other blue information panels

**Files Modified:**
- `utils/custom_styles.py` - New CSS styling module
- `app.py` - Applied custom styles globally

**Visual Impact:**
- Before: Light blue text on blue background (poor contrast)
- After: White text on blue background (excellent contrast)

**Backward Compatibility:**
- ✅ No functional changes
- ✅ Pure CSS styling enhancement
- ✅ No impact on saved models or calculations

---

## 🔧 Technical Changes

### New Files Created:
1. **`utils/period_labels.py`**
   - Generates calendar-based period labels
   - Functions: `generate_period_labels()`, `get_period_label()`, `format_dataframe_with_period_labels()`
   - Handles month/year rollover logic

2. **`utils/custom_styles.py`**
   - Custom CSS for improved readability
   - Applies white text to blue info panels

3. **`CHANGELOG_v1.1.md`**
   - This document

### Dependencies Added:
- `python-dateutil>=2.8.0` (for date calculations in period labels)

### Session State Variables Added:
- `projection_start_month` (int, 1-12, default: 1)
- `projection_start_year` (int, default: current year)

---

## 📊 Testing & Verification

### Tested Scenarios:
✅ New expense creation defaults to $0
✅ Calendar labels display correctly in monthly mode
✅ Calendar labels display correctly in annual mode
✅ Month rollover works correctly (Dec → Jan)
✅ Year rollover works correctly (Dec 2026 → Jan 2027)
✅ Charts display calendar labels on X-axis
✅ Excel exports include calendar labels
✅ Existing saved models load correctly
✅ Info panel text is readable (white on blue)
✅ All pages maintain existing functionality

### Backward Compatibility Verified:
✅ Models saved in v1.0 load correctly in v1.1
✅ All financial calculations produce identical results
✅ No breaking changes to JSON scenario format
✅ Default values applied automatically for new fields

---

## 🚀 Deployment Instructions

### For Local Development:
```bash
# Install new dependency
pip install python-dateutil>=2.8.0

# Or install all requirements
pip install -r requirements.txt

# Run application
streamlit run app.py
```

### For Render Deployment:
1. Commit all changes to repository
2. Push to main branch
3. Render will automatically detect `requirements.txt` changes
4. Deployment will install python-dateutil automatically
5. Application will restart with v1.1 features

### Verification Steps:
1. Open Home page → Verify "Projection Start Date" section appears
2. Add new Operating Expense → Verify default is $0.00
3. Build model in Review page → Verify calendar labels (e.g., "Jan 2026")
4. Check any blue info panel → Verify white text is readable
5. Load an old saved model → Verify it works correctly

---

## 📝 User-Facing Changes

### What Users Will Notice:

**Immediate:**
- New "Projection Start Date" settings on Home page
- Calendar-based column headers everywhere (Jan 2026, Feb 2026, etc.)
- Much more readable blue information panels
- New expenses start at $0 instead of $1,000

**Benefits:**
- **Better Context**: "Jan 2026" is more meaningful than "Period 1"
- **Easier Planning**: Align projections with actual business calendar
- **Improved Readability**: White text on blue is much easier to read
- **Cleaner Data Entry**: No more forgetting to change $1,000 defaults

**No Learning Curve:**
- All existing features work exactly the same
- New settings have sensible defaults
- No training required

---

## 🐛 Known Issues

None identified in v1.1.

---

## 📞 Support

For questions or issues with v1.1:
- Check this changelog for feature details
- Review the main README.md for general usage
- Contact development team for technical support

---

## 🔮 Future Enhancements (Not in v1.1)

Potential features for future versions:
- Custom fiscal year start (e.g., July 1)
- Quarterly view mode
- Multi-year comparison charts
- Additional chart customization options

---

**Version**: 1.1.0  
**Release Date**: January 2026  
**Previous Version**: 1.0.0  
**Compatibility**: Fully backward compatible with v1.0 models
