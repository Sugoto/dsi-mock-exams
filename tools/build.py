"""Builds data/sets.js. Numeric answer keys come from sim.py, never from hand arithmetic.

Run:  python3 tools/build.py
"""
import json
import random
from pathlib import Path

import sim

ROOT = Path(__file__).resolve().parent.parent
ASCENDING = "Count queue contents oldest first."
TWOQ_RULES = (
    "Use these 2Q rules: both queues share the stated capacity; a page's first reference loads it "
    "into the FIFO queue; a hit on a FIFO page moves it to the most-recent end of the LRU queue; "
    "a hit on an LRU page moves it to the most-recent end; on a miss with a full buffer, evict the "
    "oldest FIFO page if FIFO is nonempty, otherwise the least-recently-used LRU page. No page is pinned."
)


def tf(topic, answer, text, why):
    return {"type": "tf", "topic": topic, "answer": answer, "text": text, "why": why}


# ---------------------------------------------------------------------------
# Module true/false pools (20 + 15 + 15 + 15 + 15 + 10 + 10 = 100)
# ---------------------------------------------------------------------------
REL = "Relational model & SQL"
RELATIONAL = [
    tf(REL, True, "Inserting a new row into Users changes the relation's instance but not its schema.",
       "The schema is the logical design (attributes, types, constraints). An instance is the set of tuples at a moment, so inserts change only the instance."),
    tf(REL, False, "A candidate key may contain a proper subset of attributes that is itself a superkey.",
       "A candidate key is a minimal superkey: no proper subset of it uniquely identifies tuples."),
    tf(REL, True, "Under set semantics, the set of all attributes of a relation is always a superkey.",
       "Tuples in a relation are distinct, so the full attribute set always identifies each tuple."),
    tf(REL, False, "In SQL, SELECT Location FROM Users returns each distinct location only once, even without DISTINCT.",
       "SQL uses bag (multiset) semantics by default. Relational-algebra projection removes duplicates; SQL needs SELECT DISTINCT for that."),
    tf(REL, True, "A natural join of Posts(PostID, UserID, Text) and Likes(PostID, UserID) matches rows only when both PostID and UserID are equal.",
       "A natural join equates every attribute name the two schemas share, here both PostID and UserID."),
    tf(REL, False, "A LEFT OUTER JOIN of Users with Posts can return fewer rows than Users has.",
       "Every left row appears at least once: matched rows appear once per match, and unmatched rows appear padded with NULLs."),
    tf(REL, True, "WHERE filters individual rows before grouping, while HAVING filters groups after the aggregates are computed.",
       "WHERE runs before GROUP BY, and HAVING applies to the grouped results, so HAVING can reference aggregates such as COUNT(*)."),
    tf(REL, False, "COUNT(Location) includes rows whose Location is NULL.",
       "COUNT(column) skips NULLs. COUNT(*) counts all rows."),
    tf(REL, True, "A many-to-many enrollment between Students and Courses is normally stored in a separate table whose key combines StudentID and CourseID.",
       "A junction table holds one row per (student, course) pair. Neither entity table can hold the relationship in a single atomic column."),
    tf(REL, True, "A column that stores the string '3,7,9' as a list of tag IDs violates the atomic-value requirement of first normal form.",
       "First normal form (Codd's simple domains) requires atomic values. A packed list also can't be checked by a foreign key."),
    tf(REL, False, "The selection σ_age>30(Users) can contain more tuples than Users.",
       "Selection only keeps or drops tuples, so its result is a subset of the input."),
    tf(REL, True, "The Cartesian product of a relation with 4 tuples and an empty relation is empty.",
       "|R × S| = |R| · |S| = 4 · 0 = 0."),
    tf(REL, False, "A primary-key column may contain NULLs as long as all of its non-NULL values are unique.",
       "Primary-key attributes must be NOT NULL. A NULL can't identify a tuple."),
    tf(REL, True, "With ON DELETE CASCADE on the foreign key Posts.UserID → Users.UserID, deleting a user also deletes that user's posts.",
       "CASCADE propagates the delete to the referencing rows instead of rejecting it or leaving dangling references."),
    tf(REL, False, "The projection Π_UserID(Posts) always has the same number of tuples as Posts.",
       "Projection under set semantics removes duplicates. A user with several posts appears once."),
    tf(REL, True, "Relational-algebra union requires both inputs to have the same arity and compatible attribute domains.",
       "Union, intersection and difference are defined only for union-compatible relations."),
    tf(REL, False, "A foreign key from Posts.UserID to Users.UserID prevents two posts from having the same UserID.",
       "A foreign key only requires each value to exist in Users. Many posts can reference the same user; uniqueness would need a UNIQUE or primary-key constraint."),
    tf(REL, True, "A declarative query states what result is wanted and leaves access-path choices, such as index versus full scan, to the DBMS.",
       "That separation of what from how is the data-independence benefit of declarative languages like SQL."),
    tf(REL, False, "If R has 6 tuples and S has 3 tuples, an equi-join of R and S on one attribute contains at most 6 tuples.",
       "With duplicate join values, each matching pair produces a row. The upper bound is 6 × 3 = 18."),
    tf(REL, True, "SELECT PostID, COUNT(*) FROM Likes GROUP BY PostID returns no row for a post that has zero likes.",
       "Grouping only sees PostIDs present in Likes. Reporting zero counts needs an outer join with Posts."),
]

TX = "Transactions & recovery"
ACID = [
    tf(TX, True, "Atomicity means a transaction's writes take effect all together or not at all.",
       "A failed or aborted transaction leaves no partial effects."),
    tf(TX, False, "Isolation is the ACID property that guarantees committed data survives a power failure.",
       "That's durability. Isolation makes concurrent transactions behave as if they ran one at a time."),
    tf(TX, True, "Under write-ahead logging, the log record for an update must reach durable storage before the modified data page overwrites the old version on disk.",
       "If the page reached disk first and the system crashed, recovery would have no record with which to undo or redo the change."),
    tf(TX, True, "A DBMS may acknowledge COMMIT once the commit log record is durable, even if the modified data pages are still dirty in the buffer pool.",
       "Redo from the durable log can rebuild the committed changes after a crash, so data pages can be written lazily."),
    tf(TX, False, "During crash recovery, a transaction that has update records but no commit record should be redone so that no work is lost.",
       "Without a commit record the transaction never committed, so recovery must undo its effects."),
    tf(TX, False, "Durability by itself prevents two concurrent deposits from overwriting each other's update.",
       "Lost updates are an isolation failure. Both deposits can commit durably and one can still overwrite the other."),
    tf(TX, False, "Overwriting a data file in place with a single large write() call guarantees that concurrent readers and post-crash readers never see a partially updated file.",
       "An in-place write can be observed mid-way or torn by a crash. Writing a temporary file and then atomically renaming it over the original gives readers either the old file or the new file."),
    tf(TX, True, "A transaction that is atomic and durable can still violate consistency if it leaves a foreign key pointing at a row that no longer exists.",
       "Consistency means every declared constraint holds after the transaction. Atomicity and durability don't check constraints."),
    tf(TX, True, "To undo an uncommitted update after a crash, recovery needs the update's old value (its before-image) or equivalent information.",
       "Undo restores the previous state. Without before-images there's nothing to restore."),
    tf(TX, False, "If the disk guarantees every single page write is all-or-nothing, a transaction that updates three pages needs no log to be atomic.",
       "A crash can occur between page writes, leaving one page new and two old. Making several pages atomic together needs a log or a similar mechanism."),
    tf(TX, False, "An aborted transaction's partial writes may remain in the database after recovery, as long as they violate no constraint.",
       "An abort must leave no trace. Remaining partial writes would break atomicity."),
    tf(TX, True, "Without isolation, a transfer that has debited A but not yet credited B can be seen by another transaction that sums A + B and finds money missing.",
       "That's an inconsistent read of intermediate state, which isolation prevents."),
    tf(TX, False, "Forcing every dirty data page to disk at commit is the only way to guarantee durability.",
       "A durable log of the changes (redo) is enough. Forcing data pages at commit is one option, not the only one."),
    tf(TX, True, "A committed transaction's effects must survive a crash that happens immediately after COMMIT returns to the client.",
       "Once commit is acknowledged, durability requires that the effects persist."),
    tf(TX, False, "Consistency is enforced by the DBMS alone, so an application invariant such as 'transfers conserve total money' can't be broken by a transaction that commits successfully.",
       "The DBMS enforces declared constraints. Application invariants depend on the transaction logic being correct, so a buggy transfer can commit and break them."),
]

ST = "Storage & serialization"
STORAGE = [
    tf(ST, False, "Writing the raw sizeof(std::string) bytes of a std::string object to a file persists the string's characters.",
       "A std::string holds a pointer, size and capacity (characters may live on the heap). Raw bytes of the object don't portably contain the characters; serialize the length and the characters instead."),
    tf(ST, True, "A length prefix before a variable-length field lets the deserializer jump to the next field without scanning for a delimiter.",
       "Read the length, skip that many bytes, and you're at the next field."),
    tf(ST, True, "A std::unique_ptr can be moved to a new owner but not copied.",
       "unique_ptr expresses single ownership. Its copy constructor is deleted and its move constructor transfers ownership."),
    tf(ST, False, "Returning a reference to a local variable is safe as long as the caller uses it immediately.",
       "The local is destroyed when the function returns, so the reference dangles right away, however soon it is used."),
    tf(ST, True, "Destructors of stack objects run during stack unwinding when an exception propagates out of their scope.",
       "This is why RAII guards, such as lock and page guards, release resources even on error paths."),
    tf(ST, False, "static_cast from a base-class pointer to a derived-class pointer checks at runtime that the object really is of the derived type.",
       "static_cast does no runtime check. dynamic_cast does, for polymorphic types."),
    tf(ST, True, "Deleting a derived object through a base-class pointer is well-defined only if the base class has a virtual destructor.",
       "Without a virtual destructor the derived destructor isn't called, which is undefined behavior."),
    tf(ST, True, "If tuples are deleted from a page in memory and the page is never written back, reloading that page from disk brings the deleted tuples back.",
       "Disk still holds the old page image. Changes persist only after the page is serialized and written."),
    tf(ST, False, "Solid-state drives are volatile storage, so their contents are lost when power is removed.",
       "SSDs (NAND flash) are nonvolatile. DRAM is the volatile tier."),
    tf(ST, True, "On a magnetic disk, reading many randomly placed pages takes longer than reading the same number of consecutive pages.",
       "Each random read pays seek time and rotational latency; sequential reads mostly avoid both."),
    tf(ST, False, "DRAM reads and SSD reads have roughly the same latency, so keeping pages in memory mainly saves CPU time.",
       "DRAM is on the order of 100 ns; SSD reads are tens of microseconds or more. Avoiding storage reads is the main win."),
    tf(ST, True, "Storing each relation in its own file lets the system drop a relation by deleting a single file.",
       "That's an advantage of file-per-relation layouts. A single large file needs internal bookkeeping instead."),
    tf(ST, True, "A positional read such as pread(fd, buf, n, offset) doesn't change a file position shared with other threads, unlike seek followed by read.",
       "The offset is an explicit argument, so concurrent readers don't race on the shared file position."),
    tf(ST, True, "A type tag stored before each serialized field lets the deserializer decide how to interpret the bytes that follow.",
       "Self-describing encodings record which type, and therefore which decoding, applies to each field."),
    tf(ST, False, "Two processes can safely exchange in-memory objects by writing the objects' pointer values into a shared file.",
       "Addresses are only meaningful inside the process that created them. The data itself must be serialized."),
]

SP = "Slotted pages & file layout"
SLOTTED = [
    tf(SP, False, "In a slotted page, each slot entry stores its tuple's full payload, so the data region at the end of the page is only free space.",
       "A slot entry is metadata: it records where the tuple's bytes begin and how long they are. The payload lives in the tuple-data region."),
    tf(SP, True, "After compaction moves a tuple to a new byte offset, only that tuple's slot entry must change for (page_id, slot_id) references to stay valid.",
       "That one level of indirection is the point of slots: external references name the slot, not the byte offset."),
    tf(SP, True, "In the usual slotted-page layout, free space lies between the end of the slot directory and the start of the tuple-data region.",
       "The directory grows forward from the header and tuples grow backward from the end of the page."),
    tf(SP, False, "A new tuple always fits in a slotted page when the contiguous free space is at least the tuple's size, even if the insert also needs a new slot entry.",
       "A new slot entry also consumes free space. The insert needs room for the tuple bytes plus the slot entry."),
    tf(SP, True, "Before a deleted slot is reused, index entries still pointing at that (page, slot) must be removed, or lookups could return the new, unrelated tuple.",
       "Otherwise a stale index entry would silently resolve to whatever tuple now occupies the slot."),
    tf(SP, True, "In a file of fixed-size pages numbered from 0, a newly appended page starts at byte offset num_pages × PAGE_SIZE.",
       "Existing pages occupy bytes 0 to num_pages × PAGE_SIZE − 1, so the next page starts right after them."),
    tf(SP, False, "If pages within one file have different sizes, page k still begins at byte offset k × PAGE_SIZE.",
       "That formula only holds when every page has the same size. Variable sizes need a directory of offsets."),
    tf(SP, True, "An index builder that scans pages must skip empty or deleted slots; otherwise it may index tuples that no longer exist.",
       "Only active slots hold live tuples."),
    tf(SP, False, "Building a hash index over a heap file reorders the tuples on disk by key.",
       "A secondary index stores key → location entries. The heap file's physical order is unchanged."),
    tf(SP, False, "A hash index answers a range query such as key BETWEEN 10 AND 50 as efficiently as a point lookup.",
       "Hashing scatters neighboring keys across slots. Ranges need an ordered structure such as a B+-tree, or a full scan."),
    tf(SP, False, "Marking a slot empty on delete immediately makes its bytes part of the contiguous free region, available to a large new tuple.",
       "The hole stays where it is (fragmentation) until the page is compacted."),
    tf(SP, True, "A page of fixed-length records can track deleted slots with a free list, so inserts reuse holes before using never-used slots.",
       "Deleted slots are chained together, and inserts take the head of the chain."),
    tf(SP, True, "When many relations share one large database file, the DBMS, not the OS file system, must track which pages belong to which relation.",
       "The OS sees one file, so page ownership is metadata the DBMS has to keep itself."),
    tf(SP, False, "In a slotted page, deleting the tuple in slot 2 requires renumbering slots 3, 4 and 5 so slot ids stay contiguous.",
       "Renumbering would break every (page, slot) reference. The slot is simply marked empty."),
    tf(SP, True, "A map from page id to an in-memory page lets the storage layer serve repeated requests without re-reading the page from disk.",
       "A hit in the map avoids storage I/O. Only misses read from disk."),
]

HX = "Hash tables (M7)"
HASHING = [
    tf(HX, True, "With linear probing, a long run of occupied slots tends to keep growing, because any key that hashes anywhere into the run lands at its end.",
       "This is primary clustering, and it lengthens probe sequences."),
    tf(HX, False, "As the load factor of an open-addressing table approaches 1, the expected number of probes per insert stays roughly constant.",
       "It rises sharply: with few free slots, inserts must probe much further to find one. That's why tables are resized before they fill up."),
    tf(HX, True, "With table size 10 and quadratic probing (h + i²) mod 10, an insert can fail to find a free slot even though the table still has empty slots.",
       "i² mod 10 only takes the values {0, 1, 4, 5, 6, 9}, so some offsets are never probed."),
    tf(HX, True, "In double hashing, if h2(k) shares a common factor with the table size, the probe sequence for k visits only some of the slots.",
       "The step cycles with period size / gcd(h2(k), size)."),
    tf(HX, False, "An insert that reaches a tombstone may store the key there immediately, without checking whether the same key appears later in its probe sequence.",
       "The key might already exist further along the chain. Storing it at the tombstone would create a duplicate, so the insert must keep probing first."),
    tf(HX, True, "Rebuilding an open-addressing table by reinserting only the live keys removes every tombstone.",
       "Tombstones aren't copied, so probe chains get shorter again."),
    tf(HX, True, "If h(key) = key mod 8 and every inserted key is a multiple of 8, all keys share one home slot.",
       "Every key mod 8 = 0, so a poor key distribution defeats the hash function."),
    tf(HX, False, "A lookup in a linear-probing table can stop at the first tombstone, because the key would have been stored there if it existed.",
       "The key may have been inserted before the deletion that created the tombstone, so it can sit further along. Only a never-used slot ends the search."),
    tf(HX, False, "Deleting a key by resetting its slot to never-used is safe in linear probing as long as the table is less than half full.",
       "Load factor doesn't matter. Any key that probed past that slot becomes unreachable."),
    tf(HX, True, "In linear probing, an unsuccessful lookup whose home slot has never been used costs exactly one probe.",
       "The first probe hits a never-used slot, which proves the key is absent."),
    tf(HX, False, "Double hashing uses the same step size for every key, just like linear probing.",
       "The step is h2(k), which varies by key. That's what breaks up primary clusters."),
    tf(HX, True, "A prime table size helps double hashing, because then every step size from 1 to size − 1 visits every slot.",
       "With a prime size, gcd(step, size) = 1 for every nonzero step."),
    tf(HX, True, "A table with many tombstones and few live keys can still have long unsuccessful lookups.",
       "Lookups probe past tombstones and stop only at never-used slots."),
    tf(HX, False, "Hashing preserves key order, so reading slots 0 through n − 1 returns the keys sorted.",
       "Hash functions scatter keys. Slot order has nothing to do with key order."),
    tf(HX, True, "A hash index typically maps a search key to tuple locations such as (page_id, slot_id) instead of storing whole tuples.",
       "The index stores pointers back into the data pages, so tuples aren't duplicated."),
]

BM = "Buffer management"
BUFFER = [
    tf(BM, True, "A frame whose pin count is greater than zero must not be chosen as an eviction victim.",
       "A pin means some thread is using the frame right now. Evicting it would pull the page out from under that thread."),
    tf(BM, False, "Evicting a clean page requires writing it back to disk first.",
       "A clean page matches its disk copy, so the frame can simply be reused."),
    tf(BM, False, "In 2Q, when the FIFO queue holds an unpinned page, the victim is still taken from the LRU queue first.",
       "2Q evicts from FIFO first. Pages that have proven reuse in the LRU queue are protected."),
    tf(BM, True, "In 2Q, a long sequential scan that touches each page once mostly cycles through the FIFO queue, protecting the pages in the LRU queue.",
       "Pages touched once never get promoted, so they flow through FIFO and get evicted there. This is how 2Q resists buffer-pool flooding."),
    tf(BM, True, "Separating policy from mechanism lets the buffer manager switch from LRU to 2Q without changing how frames are read, written or pinned.",
       "The policy only chooses the victim. The mechanism (I/O, pinning, write-back) stays the same."),
    tf(BM, True, "Holding the buffer manager's global lock while waiting for a disk read makes unrelated page requests wait behind slow I/O.",
       "That's why the lab requires releasing the coarse lock before doing disk I/O."),
    tf(BM, False, "Copying a PageGuard is safe because each copy unfixes the page once when destroyed.",
       "Two copies would unfix twice, decrementing the pin count too far. PageGuard is move-only."),
    tf(BM, True, "If a page is unfixed with is_dirty = true, its frame must stay marked dirty until its contents are written back.",
       "Clearing the flag early would let eviction drop the modification."),
    tf(BM, False, "With MAX_PAGES = 1000, page_id 1000 is the last valid page.",
       "Valid ids are 0 to 999, and fix_page must reject 1000 as out of range."),
    tf(BM, True, "On the same reference trace, giving an LRU buffer more frames never increases the number of misses.",
       "LRU is a stack algorithm: the contents of a smaller LRU cache are always a subset of a larger one's."),
]

MT = "Multi-threading & concurrent indexes"
THREADS = [
    tf(MT, True, "A data race happens when two threads access the same memory location without synchronization and at least one of the accesses is a write.",
       "Concurrent reads alone are fine. A race needs a shared location and at least one write."),
    tf(MT, True, "Unlike std::lock_guard, std::unique_lock can release its mutex before the end of its scope.",
       "unique_lock supports unlock() and relocking. lock_guard only releases in its destructor."),
    tf(MT, True, "std::scoped_lock can lock two mutexes at once using a deadlock-avoidance algorithm.",
       "It acquires all the mutexes as if with std::lock, so two threads naming the same pair in different orders won't deadlock."),
    tf(MT, False, "Declaring a shared counter volatile makes counter++ safe across threads.",
       "volatile doesn't make operations atomic or synchronize threads. Use std::atomic or a mutex."),
    tf(MT, True, "Under a reader/writer lock, two readers of the same slot can proceed together, but a writer to that slot must wait for both.",
       "Shared (read) mode is compatible with other readers. Exclusive (write) mode is compatible with no one."),
    tf(MT, False, "Adding more threads than CPU cores always speeds up a CPU-bound index build.",
       "Beyond the core count, threads compete for the same cores and context switching adds overhead."),
    tf(MT, True, "If 50% of a job must run serially, no number of threads can make it more than 2× faster.",
       "By Amdahl's law, speedup ≤ 1 / serial fraction = 1 / 0.5 = 2."),
    tf(MT, True, "In a hash index with one lock per slot, an insert whose probe sequence crosses several slots may need to lock more than one slot.",
       "Probing reads neighboring slots that other threads may be changing, so they need protection too."),
    tf(MT, False, "A bug that appears only under particular thread interleavings will reproduce reliably on every run.",
       "Interleavings vary from run to run (heisenbugs). That's why race detectors and stress tests matter."),
    tf(MT, True, "Under one global index mutex, two lookups for keys in different slots still execute one at a time.",
       "A single mutex serializes every operation, whatever slot it touches."),
]


HX7 = "Hash tables (M7)"
HASH7 = [
    tf(HX7, True, "Open-addressing deletes need at least three slot states (never used, occupied, deleted/tombstone) to keep lookups correct.",
       "With only empty and occupied, a delete would either break probe chains (if marked empty) or never free the slot."),
    tf(HX7, False, "In open addressing, a key's final slot depends only on its own hash value, not on which keys were inserted before it.",
       "Earlier keys occupy slots along the probe sequence, so the same key can land in different slots depending on insertion history."),
    tf(HX7, True, "If an entry also stores its key's home slot, (slot − home) mod capacity tells how many positions past home the key was placed by linear probing.",
       "That displacement is the number of extra probes a successful lookup of that key will make."),
    tf(HX7, False, "With double hashing p_i(k) = (h1(k) + i·h2(k)) mod m, the third probe position can only be found by first computing the first and second probes.",
       "Each position has a closed form: p_i = (h1 + i·h2) mod m, so any probe position can be computed directly."),
    tf(HX7, True, "Inserting the same two colliding keys in the opposite order into an empty linear-probing table can swap which slot each key ends up in.",
       "Whichever key arrives first takes the home slot, and the second goes to the next free slot."),
    tf(HX7, False, "A lookup that returns std::optional<Value> still needs a sentinel value such as −1 to signal that a key is missing.",
       "std::nullopt represents absence, so no sentinel has to be reserved from the value domain."),
    tf(HX7, True, "A hash index backed by a std::vector sized once at construction can't hold more entries than its capacity without being rebuilt into a larger vector.",
       "Open addressing stores entries in the array itself, so growing it means allocating a bigger array and rehashing."),
    tf(HX7, False, "h2(k) = k mod m is a safe secondary hash for double hashing.",
       "It returns 0 for every multiple of m, and a step of 0 probes the same slot forever. That's why definitions use 1 + (k mod m′)."),
    tf(HX7, False, "Inserting a key that already exists in an open-addressing table should add a second entry at the first free slot of its probe sequence.",
       "The insert should find the existing entry and update it in place, otherwise lookups return a stale value and the table holds duplicates."),
    tf(HX7, True, "Two keys with the same h1 but different h2 values follow different probe sequences after their first probe under double hashing.",
       "Both start at h1, but then step by different amounts, which is how double hashing avoids secondary clustering."),
]

TS = "Thread-safe hash table (M8)"
HASH8 = [
    tf(TS, True, "A std::shared_lock on a std::shared_mutex holds it in shared mode, so many lookups can hold it at the same time.",
       "Shared mode is compatible with other shared holders. Only exclusive mode excludes everyone."),
    tf(TS, False, "A thread holding a shared lock on a std::shared_mutex can safely upgrade to exclusive mode by calling lock() on the same mutex.",
       "std::shared_mutex has no upgrade. Calling lock() while holding a shared lock deadlocks or is undefined; the thread must release the shared lock first."),
    tf(TS, True, "If two threads each hold a shared lock on the same std::shared_mutex and both then wait for the exclusive lock, they can deadlock.",
       "Each waits for the other to release its shared hold, and neither does. This is the classic upgrade deadlock."),
    tf(TS, True, "For a read-mostly workload, one table-wide std::shared_mutex can outperform one table-wide std::mutex, because lookups no longer run one at a time.",
       "Readers share the lock. With a plain mutex every lookup serializes."),
    tf(TS, False, "For a workload in which every operation is an insert, replacing a global std::mutex with a global std::shared_mutex substantially increases throughput.",
       "Inserts need exclusive mode, so they still run one at a time, and shared_mutex bookkeeping can even add overhead."),
    tf(TS, False, "Under per-slot locking, an insert that probes slots 4, 5 and 6 can release slot 4's lock before examining slot 5 with no risk of races, because only the final slot is written.",
       "Releasing early lets another thread change the probe chain mid-insert, for example inserting the same key, so the insert can create a duplicate or miss an existing entry."),
    tf(TS, True, "If every thread acquires slot locks in increasing slot order, two threads following that rule can't form a circular wait on those locks.",
       "A global lock order removes the circular-wait condition for deadlock."),
    tf(TS, False, "Lock striping, with one lock per group of slots, allows more parallelism than one lock per slot.",
       "Striping trades parallelism for fewer lock objects: unrelated slots in the same stripe now contend."),
    tf(TS, True, "With 4 lock stripes and stripe = slot mod 4, operations on slots 1 and 5 contend for the same lock.",
       "1 mod 4 = 5 mod 4 = 1, so both slots share stripe 1."),
    tf(TS, True, "A lookup that skips locking can observe a half-written entry while another thread is inserting into that slot.",
       "The key and value writes aren't atomic as a pair, so an unsynchronized reader can see the new key with the old value, a data race."),
    tf(TS, True, "If every request hashes to the same slot, per-slot locking behaves roughly like a single global lock.",
       "All requests contend for one lock, so finer granularity buys no parallelism."),
    tf(TS, False, "A std::shared_mutex lets a writer in exclusive mode proceed while readers still hold it in shared mode.",
       "Exclusive mode waits until every shared holder has released the mutex."),
]

THREADS_GENERAL_IDX = [0, 1, 2, 3, 5, 6, 8]
THREADS_INDEX_IDX = [4, 7, 9]

# ---------------------------------------------------------------------------
# Paper true/false (50, grouped by paper)
# ---------------------------------------------------------------------------
P1, P2, P3, P4 = ("Codd 1970", "Stonebraker 1981", "Stonebraker & Pavlo 2024", "Umbra 2020")
PAPER_NOTES = {
    P1: "E. F. Codd, A Relational Model of Data for Large Shared Data Banks (CACM 1970)",
    P2: "M. Stonebraker, Operating System Support for Database Management (CACM 1981)",
    P3: "M. Stonebraker & A. Pavlo, What Goes Around Comes Around... And Around... (SIGMOD Record 2024)",
    P4: "T. Neumann & M. Freitag, Umbra: A Disk-Based System with In-Memory Performance (CIDR 2020)",
}
PAPERS = [
    # ---- Codd 1970 ----
    tf(P1, False, "Codd says programs written for IDS keep working when its indexing chains are removed, because an index is a purely performance-oriented, redundant structure.",
       "§1.2.2: IDS programs that use indexing chains must refer to them by name, so they fail when the chains are removed. TDMS (indexes on every attribute) and IMS (no index or primary-key index only) don't have this problem. Indexing is one of three dependencies Codd wants removed, with ordering and access-path dependence."),
    tf(P1, True, "In Codd's array picture of a relation, row order is immaterial but column order is significant. For users, he proposes domain-unordered 'relationships' in which repeated domains get role names.",
       "§1.3: column order matters because two columns can share a domain (component(part, part, quantity)). Users shouldn't have to remember the order of, say, 30 domains, so they work with relationships and role names like sub.part and super.part."),
    tf(P1, False, "In Codd's parts-and-projects example, a program written for one of the five tree structures fails on at most one of the other four.",
       "§1.2.3: it fails on at least three of the remaining structures. If it works on structure 5, it fails on all the others. This is access-path dependence, and keeping every old path forever isn't practical."),
    tf(P1, True, "In Codd's supply(supplier, part, project, quantity) relation, the combination of supplier, part and project is the primary key, and each of those three domains on its own is a foreign key.",
       "§1.3. A foreign key isn't the primary key of R, but its values are primary-key values of some relation S, and S may be R itself. A primary key is nonredundant if no participating domain is superfluous."),
    tf(P1, False, "Codd's normalization procedure applies to any unnormalized collection, including one where a primary key has a nonsimple component domain.",
       "§1.4 has two preconditions: the nonsimple domains must form a collection of trees, and no primary key may have a nonsimple component. Normalization copies the parent's key into each child, adds it to the child's key, and strikes out the nonsimple domains."),
    tf(P1, True, "Codd says a first-order predicate calculus is enough for his universal data sublanguage, provided the collection of relations is in normal form.",
       "§1.5. The sublanguage's universality lies in its descriptive ability, not its computing ability. Arithmetic functions are defined in the host language and invoked from the sublanguage."),
    tf(P1, False, "Codd says that symmetric exploitation of an n-ary relation in a path-based system needs 2n − 1 named paths.",
       "§1.5: it needs n! paths (2 for a binary relation). The 2n − 1 figure is something else: the number of names needed when an n-ary relation is written as nested binary relations, compared with n + 1 in n-ary notation (7 vs 5 for supply)."),
    tf(P1, True, "Codd describes the named set of relations as a subset of the expressible set, and usually a very small one.",
       "§1.6. The named set holds relations users can refer to by a simple name. The expressible set holds every relation the data language can describe from those names, connectives and quantifiers."),
    tf(P1, True, "Codd says that if S is a function, there's no point of ambiguity, so the natural join of R with S is the only join of R with S.",
       "§2.1.3: a point of ambiguity is a joining-domain value with more than one relative under both R and S. It causes multiple joins. Joinability is not symmetric: joining R with S is a separate question from joining S with R."),
    tf(P1, False, "Codd shows that when R and S have several distinct joins, they always have exactly as many distinct compositions.",
       "§2.1.4: the number of compositions can be as few as one or as many as the number of joins (Fig. 12 has many joins and one composition). Confusing compositions with path-following leads to the 'connection trap'."),
    tf(P1, False, "Codd's adequate set of operations for derivability in the named set includes permutation and natural composition.",
       "§2.2: the set is projection, natural join, tie and restriction. Permutation is irrelevant to domain-unordered relationships, and natural composition is just a natural join followed by a projection. Plain 'join' isn't eligible because its result isn't unique."),
    tf(P1, True, "Codd says weak redundancies can't be removed by the database administrator and, if present, appear in both the named set and the stored set.",
       "§2.2.2: weak redundancy is inherent in users' logical needs (e.g. P is always some composition of Q and R, not necessarily the natural one). Strong redundancy can be expressed as an equation, and may be kept on purpose so old programs keep running."),
    tf(P1, False, "Codd recommends checking consistency on every insertion, deletion and key update rather than in a daily batch, because batch checking can't trace which input caused an inconsistency.",
       "§2.3: with a journal of state-changing transactions, batch checking can track down the inputs, and it's superior if few lasting inconsistencies occur. Per-operation checking slows those operations down. Consistency is a property of the current state, whether it came from omission or commission."),

    # ---- Stonebraker 1981 ----
    tf(P2, False, "Stonebraker reports that on a PDP-11/70, fetching 1 byte from the UNIX buffer pool costs about the same as fetching 512 bytes: over 5,000 instructions.",
       "§2.1: 512 bytes costs over 5,000 instructions and 1 byte about 1,800 (system call plus core-to-core copy). He says an OS buffer manager would need a few hundred instructions to be attractive, so INGRES and System R keep their own pool in user space."),
    tf(P2, True, "For random accesses to blocks that won't be referenced again, Stonebraker recommends toss-immediately rather than LRU.",
       "§2.2 lists four access patterns. LRU suits only random access with a nonzero chance of re-reference. One-time sequential and random access should toss immediately. For cyclic sequential access LRU is the worst possible policy, unless all n pages fit."),
    tf(P2, False, "The study Stonebraker cites found that a DBMS-specific replacement policy cut the buffer miss ratio by about half compared with LRU.",
       "Kaplan's INGRES traces showed a 10–15% cut. Stonebraker adds that an OS buffer manager would need a way to accept replacement 'advice' from the DBMS."),
    tf(P2, True, "In the intentions-list scheme Stonebraker describes, the transaction isn't reliably committed, and the user can't be told it succeeded, until the commit flag reaches disk.",
       "§2.4. The commit-flag page must be forced after all intentions-list pages, which requires a 'selected force out' that no OS buffer manager he knew of provided. Processing the list is made idempotent so recovery can redo it."),
    tf(P2, True, "Stonebraker says a DBMS prefers an extent-based file system, because files grown a block at a time scatter their blocks and sequential scans then cause heavy disk-arm movement.",
       "§3.1. Extent-based files grow an extent at a time and can be read as a contiguous collection. Stonebraker also says OS designers should provide record management as the lower-level object and character arrays on top of it."),
    tf(P2, False, "Stonebraker counts two separately managed tree structures when INGRES runs on UNIX: the i-node's indirect-block tree and INGRES's own keyed-access tree.",
       "§3.2 counts three: the file's block tree (i-node), the directory hierarchy, and the DBMS's ISAM or B-tree index. He argues one combined tree would be more efficient."),
    tf(P2, True, "Because UNIX had no shared data segments, INGRES had to put its lock table inside the operating system and give each user private buffering.",
       "§4. In a process-per-user design the buffer pool and lock table should ideally be shared segments, as in System R. The alternative is a single server process, as in Tandem's Enscribe."),
    tf(P2, False, "Stonebraker argues that a first-come-first-served server with no internal parallelism works well on a machine with many disks, since each request can keep all the disks busy.",
       "§4.3: each request tends to have one disk read outstanding, so at most one disk is active, and long requests delay short ones. A server must otherwise do its own scheduling and multitasking, a painful duplication of OS facilities."),
    tf(P2, True, "Stonebraker warns that replacing a task switch per I/O with a message per I/O may not help, because a round-trip message on PDP-11/70 UNIX costs about 5,000 instructions.",
       "§4.4. A task switch costs from a few hundred instructions to a thousand or more on OSes with 'large' processes. Neither the process-per-user model nor the server model escapes the overhead."),
    tf(P2, False, "In Stonebraker's example of a 20% pay cut for everyone who earns more than their manager, updating rows in place as they're found is safe because Brown is the only employee who ever qualifies.",
       "§5.2: Smith earns 10,000 under Brown at 11,000. If Brown's pay is cut to 8,800 before Smith is examined, Smith now qualifies too. The outcome depends on execution order unless an intentions list defers the updates."),
    tf(P2, True, "To solve the convoy problem, Stonebraker suggests a special scheduling class in which DBMS processes are never forcibly descheduled but give up the CPU voluntarily.",
       "§4.5. A convoy forms when a process is descheduled while holding a short-term lock on the shared buffer pool. In his conclusion, he says real-time OSs with minimal, efficient services come closest to what a DBMS wants."),
    tf(P2, False, "Stonebraker says a page table describes a file of 1,000 consecutive blocks as compactly as an extent-based file control block does.",
       "§6.1: a file control block stores a starting block and a length, but a page table stores all 1,000 addresses. At 4 bytes per 4 KB page, a 100 MB file needs about 100 KB of page table, which may not stay resident and can cause a second page fault."),

    # ---- Stonebraker & Pavlo 2024 ----
    tf(P3, False, "Stonebraker and Pavlo say Google moved its crawl processing off MapReduce because MapReduce couldn't scale to the size of the crawl.",
       "§2.1: Google needed to update the crawl database interactively in real time, and MapReduce was a batch system, so the crawl moved to BigTable. MR was retired in 2014. Hadoop vendors then built SQL engines (Impala, Drill, Presto) directly on HDFS."),
    tf(P3, False, "Stonebraker and Pavlo describe column-family systems such as BigTable, Cassandra and HBase as using a columnar data model.",
       "§2.4: despite the name, column-family is a reduction of the document model with one level of nesting. Columnar storage (§3.1) is a physical layout for OLAP. Column-family systems also copied BigTable's lack of joins and secondary indexes."),
    tf(P3, True, "Stonebraker and Pavlo note that the problems with denormalizing data into nested documents date to the 1970s: data is duplicated when the relationship isn't one-to-many, prejoins aren't necessarily faster, and data independence is lost.",
       "§2.3. They see document DBMSs as repeating the object-oriented and XML DBMS arguments about removing impedance mismatch."),
    tf(P3, False, "Stonebraker and Pavlo say MongoDB was the first major NoSQL DBMS to add a SQL interface.",
       "§2.3: MongoDB was the last holdout, adding SQL for Atlas in 2021, after DynamoDB (PartiQL), Cassandra (CQL), Aerospike and Couchbase. 'NoSQL' shifted from 'don't use SQL' to 'Not only SQL'."),
    tf(P3, False, "Stonebraker and Pavlo report that, as with JSON support, major RDBMSs took several years to add vector indexes after LLMs went mainstream.",
       "§2.7: it took less than a year after ChatGPT (late 2022), partly because adding an index is little engineering and vendors integrated libraries like FAISS or DiskANN. JSON support took years. Vector DBMSs are document DBMSs with ANN indexes, and an index is a feature, not a new architecture."),
    tf(P3, True, "Stonebraker and Pavlo expect OLTP graph workloads to be served mostly by RDBMSs, and graph analytics to work best in main memory on a single node with compact, specialized data structures.",
       "§2.8–2.9. Distributed graph algorithms rarely beat single-node implementations because of communication costs. SQL:2023 added SQL/PGQ, and DuckDB's SQL/PGQ beat a leading graph DBMS by up to 10×."),
    tf(P3, True, "Stonebraker and Pavlo expect scientific applications to keep using bespoke array systems, even though SQL:2023 added multi-dimensional arrays (SQL/MDA).",
       "§2.9: array DBMSs remain a niche, and RDBMSs can't store and analyze arrays efficiently despite SQL/MDA. No major cloud provider offers a hosted array DBMS."),
    tf(P3, True, "Stonebraker and Pavlo give three advantages of column stores: better compression, inner loops that process a whole column with vectorized instructions, and very little per-record storage overhead.",
       "§3.1. A Volcano-style engine runs each operator once per row, and row stores carry about 20 bytes of header per record. Every data-warehouse vendor has moved from row stores to column stores."),
    tf(P3, False, "Stonebraker and Pavlo credit Amazon Redshift with introducing serverless computing for cloud-native DBMSs.",
       "§3.2: Snowflake introduced it. Disaggregated storage gives per-query elasticity and lets compute be reassigned, and they expect shared-disk designs to dominate rather than shared-nothing."),
    tf(P3, True, "Stonebraker and Pavlo say custom hardware accelerators for DBMSs are likely to succeed only at large cloud vendors, who can justify $50–100M of R&D and control the whole hardware and software stack.",
       "§3.5. GPU DBMSs outnumber FPGA ones because of libraries like CUDA, but a GPU stalls once data doesn't fit in its memory. Redshift AQUA is an example of cloud-vendor hardware."),
    tf(P3, False, "Stonebraker and Pavlo attribute NewSQL's weak adoption mainly to NoSQL systems already providing strong ACID transactions.",
       "§3.4: existing DBMSs were good enough, and companies are risk-averse about migrating OLTP systems. NewSQL vendors also bet wrongly on in-memory systems, since SSDs got cheaper while DRAM stayed expensive. NoSQL vendors later added transactions themselves."),
    tf(P3, True, "Stonebraker and Pavlo note that MySQL was the first DBMS to expose an API for replacing its storage manager, which let Meta replace InnoDB with RocksDB across its MySQL fleet.",
       "§2.2: using embedded key/value stores as storage managers is a 20-year trend. MongoDB similarly switched to WiredTiger in 2014. They add that an RDBMS emulates a KV store easily, but the reverse is hard."),
    tf(P3, False, "Stonebraker and Pavlo expect LLM-based natural-language interfaces to replace SQL for writing OLTP applications.",
       "§4: OLTP code generates queries through ORMs, so nobody will write it in natural language. NL may help draft exploratory OLAP queries, which should then be refined in a dashboard because natural language is ambiguous."),

    # ---- Umbra 2020 ----
    tf(P4, False, "Like the ADABAS buffer manager, Umbra requires the amount of buffer-pool memory to be configured separately for each page size class.",
       "§2/§5: Umbra uses one pool into which any size class loads, by default half of physical memory. ADABAS supported only two page sizes in separate pools sized in advance."),
    tf(P4, True, "For each size class, Umbra reserves a virtual-memory region as large as the whole buffer pool, so the virtual address space of a size class never fragments, although the physical memory behind it can.",
       "§2.1: frames hold fixed virtual addresses in a private anonymous mmap. pread fills a frame, and on eviction pwrite plus madvise(MADV_DONTNEED) releases the physical memory. Pages start at 64 KiB and double with each size class."),
    tf(P4, False, "A swizzled swip in Umbra stores a 57-bit memory pointer together with the page's 6-bit size class.",
       "§2.2: a swizzled swip is just the pointer, whose low bit is 0 because of 8-byte alignment. An unswizzled swip has its tag bit set to 1 and stores a 57-bit page number plus a 6-bit size class, enough to load the page."),
    tf(P4, True, "Umbra requires every buffer-managed data structure to organize its pages as a (possibly degenerate) tree, so each page is referenced by exactly one owning swip.",
       "§2.2: otherwise every swip pointing to a page would have to be found and updated on eviction. So B+-tree leaves have no sibling pointers, and scans keep an optimistic latch on the parent to reach the next leaf."),
    tf(P4, False, "If the state bits of an Umbra versioned latch hold the value 3, three threads currently hold the latch in shared mode.",
       "§2.3: 0 means unlocked, 1 exclusive, and n + 1 means n shared holders, so 3 means two. The latch is a 64-bit word with 5 state bits and a 59-bit version counter. Optimistic readers don't touch the latch at all; they record the version and validate it afterwards, and a page may even be evicted mid-read (the reserved virtual range then reads as zeros)."),
    tf(P4, False, "Like LeanStore, Umbra supports only optimistic latching for readers.",
       "§2.3: Umbra adds a shared mode. Its operators don't know relations are paged, so without shared latches every operator would need validation logic, and read-heavy OLAP queries would keep failing validation when other queries write."),
    tf(P4, True, "Umbra's B+-tree inner nodes always use the smallest page size, 64 KiB, giving a fanout of 8,192.",
       "§2.4. Leaves are usually 64 KiB as well, but a leaf can use a larger size class when a single tuple doesn't fit."),
    tf(P4, False, "When an Umbra leaf page overflows, the leaf is split around its median tuple identifier, as in a standard B+-tree.",
       "§2.4: tuple identifiers are synthetic 8-byte keys that increase strictly monotonically, so Umbra fills nodes completely and never splits leaves. A new leaf is allocated only when a tuple doesn't fit, and leaves use a PAX layout."),
    tf(P4, True, "In Umbra, a string of exactly 12 characters is stored entirely inside its 16-byte header.",
       "§3.1: 4 bytes of length plus up to 12 inline characters. Longer strings keep a 4-character prefix and an 8-byte offset or pointer. Strings never need to be split across pages, because pages can be larger."),
    tf(P4, False, "A string read from a relation has persistent storage duration in Umbra, because it lives in the database.",
       "§3.1: strings from relations are transient, since their page may be evicted, so they must be copied if materialized. Query constants are persistent, and strings created during the query (e.g. by UPPER) are temporary and garbage-collected."),
    tf(P4, True, "Umbra first runs each step's IR as interpreted bytecode, and compiles it with LLVM only when its adaptive execution judges that worthwhile.",
       "§3.3: Umbra generates its own lightweight IR rather than LLVM IR, and plans are modular state machines of steps processed in morsels. Adaptive compilation is largely why Umbra beats HyPer (3.0× on JOB, 1.8× on TPC-H), while raw execution times are comparable."),
    tf(P4, True, "When Umbra bypassed its buffer manager entirely and read relations from flat memory-mapped files, query execution time changed by less than 6% on average.",
       "§4.2: it changed by under 2% when only string materialization was avoided. Cold-cache scans reached 1.13 GiB/s with the buffer manager and 1.15 GiB/s without it, so storage bandwidth is the bottleneck."),
]

# ---------------------------------------------------------------------------
# Numeric questions (5 × 2 points, then 5 × 3 points per exam)
# ---------------------------------------------------------------------------
def num(topic, points, text, answer, why):
    assert isinstance(answer, int)
    return {"type": "num", "topic": topic, "points": points, "text": text, "answer": answer, "why": why}


def fmt(n):
    return f"{n:,}"


def exam1_numeric():
    q = []
    users, ins = {1, 2, 3, 5, 8}, [3, 4, 8, 9, 1, 5]
    ok = [u for u in ins if u in users]
    q.append(num(REL, 2, "Users contains UserID values {1, 2, 3, 5, 8}. Posts has a foreign key Posts.UserID → Users.UserID. The system tries to insert posts with UserID values 3, 4, 8, 9, 1 and 5. How many of these inserts satisfy the foreign key?",
                 len(ok), f"Values present in Users: {', '.join(map(str, ok))}, so {len(ok)} inserts succeed. 4 and 9 don't exist."))
    used, cap, steps = 150, 1024, []
    for t in [400, 300, 250, 120]:
        if used + t <= cap:
            used += t
            steps.append(f"+{t} → {used}")
        else:
            steps.append(f"{t} rejected ({used + t} > {cap})")
    q.append(num(SP, 2, "A page has capacity 1024 bytes and starts with used_size = 150. Tuple inserts of 400, 300, 250 and 120 bytes are attempted in that order. An insert succeeds only if used_size + tuple_size ≤ 1024; a rejected insert leaves used_size unchanged. What is the final used_size?",
                 used, "; ".join(steps) + "."))
    have, reqs, misses = {1, 4, 6}, [4, 2, 6, 7, 2, 1], []
    for r in reqs:
        if r not in have:
            misses.append(r)
            have.add(r)
    q.append(num(BM, 2, "A page map initially holds page ids 1, 4 and 6. Requests arrive for pages 4, 2, 6, 7, 2 and 1. Each miss reads one 8192-byte page from storage and adds it to the map; nothing is evicted. How many bytes are read from storage?",
                 len(misses) * 8192, f"Misses: pages {', '.join(map(str, misses))} (the second request for 2 is a hit). {len(misses)} × 8192 = {fmt(len(misses) * 8192)} bytes."))
    serial, final = 500 + 250 - 100, 500 - 100
    q.append(num(TX, 2, "A balance starts at 500. Clerk 1 reads 500 and plans to write 750 (a deposit of 250). Clerk 2 also reads 500 and plans to write 400 (a withdrawal of 100). Clerk 1 writes 750, then Clerk 2 writes 400. By how many dollars does the final balance differ from the serial result?",
                 serial - final, f"Serial result: 500 + 250 − 100 = {serial}. Clerk 2's write overwrites Clerk 1's, leaving {final}. Difference = {serial - final}."))
    keys = [12, 25, 32, 47, 55, 61, 72]
    homes = [k % 10 for k in keys]
    q.append(num(TS, 2, "A thread-safe hash index with capacity 10 uses one exclusive mutex per slot, and each insert locks only its home slot (key mod 10). Inserts for keys 12, 25, 32, 47, 55, 61 and 72 arrive at the same time. What is the largest number of these inserts whose critical sections can run at once?",
                 len(set(homes)), f"Home slots: {', '.join(map(str, homes))}. Inserts on the same slot wait for each other, so at most one per distinct slot runs: {len(set(homes))}."))

    trace = [1, 2, 3, 1, 4, 5, 2, 6, 1, 7]
    _, ev, _, _ = sim.twoq(4, trace)
    q.append(num(BM, 3, f"A 2Q buffer with capacity 4 starts empty and processes the trace {', '.join(map(str, trace))}. {TWOQ_RULES} Which page is removed by the second eviction?",
                 ev[1], f"The evictions, in order, are pages {', '.join(map(str, ev))}. Page 1 is promoted to LRU on its second reference, so the scan pages leave through FIFO."))
    trace, dirty = [1, 2, 3, 1, 4, 2, 5, 1], {2, 4}
    m, ev = sim.lru(3, trace)
    flushes = [p for p in ev if p in dirty]
    q.append(num(BM, 3, f"An LRU buffer with capacity 3 starts empty and processes the trace {', '.join(map(str, trace))}. Each miss reads one 4096-byte page. Pages 2 and 4 are dirty whenever they are evicted; all other pages are clean. Each dirty eviction writes one 4096-byte page. How many bytes are transferred in total (reads plus writes)?",
                 (m + len(flushes)) * 4096, f"{m} misses; evictions in order: {', '.join(map(str, ev))}, of which {len(flushes)} are dirty ({', '.join(map(str, flushes)) or 'none'}). ({m} + {len(flushes)}) × 4096 = {fmt((m + len(flushes)) * 4096)}."))
    slots = sim.double_hash(10, [5, 15, 25, 35], lambda k: 1 + k % 7)
    q.append(num(HX, 3, "A ten-slot table starts empty and uses h1(k) = k mod 10, h2(k) = 1 + (k mod 7) and p_i(k) = (h1(k) + i·h2(k)) mod 10. Insert keys 5, 15, 25 and 35 in that order. What is the sum of the final slots of keys 15, 25 and 35?",
                 slots[15] + slots[25] + slots[35], f"Final slots: 5→{slots[5]}, 15→{slots[15]}, 25→{slots[25]}, 35→{slots[35]}. Sum = {slots[15] + slots[25] + slots[35]}."))
    ops = [("d", 2), ("d", 5), "ins", "ins", ("d", 0), "ins", "ins"]
    q.append(num(SP, 3, "A fixed-length record page starts with slots 0–7 occupied, free-list head = −1 and next_unused = 8. A delete pushes its slot onto the front of the free list. An insert takes the free-list head, or next_unused if the list is empty. Operations: delete 2; delete 5; insert; insert; delete 0; insert; insert. Which slot receives the final insert?",
                 sim.free_list(8, ops), "Free list after the deletes: [5, 2]. The inserts take 5, then 2. Delete 0 gives [0]. The next insert takes 0 and the last one uses next_unused = 8."))
    r, s = [1, 1, 2, 3, 3, 3], [1, 2, 2, 3, 4]
    q.append(num(REL, 3, "Relation R has join-key values 1, 1, 2, 3, 3, 3. Relation S has join-key values 1, 2, 2, 3, 4. An inner join matches R.K = S.K. How many rows does it produce?",
                 sim.join_count(r, s), "Key 1: 2 × 1 = 2; key 2: 1 × 2 = 2; key 3: 3 × 1 = 3; key 4 has no match in R. Total = 7."))
    return q


def exam2_numeric():
    q = []
    existing, ins, accepted = {100, 200, 300, 400}, [200, 500, 600, 100, 700, 500], []
    for k in ins:
        if k not in existing:
            existing.add(k)
            accepted.append(k)
    q.append(num(REL, 2, "Users already contains primary keys {100, 200, 300, 400}. The system tries to insert, in order, users with keys 200, 500, 600, 100, 700 and 500. Inserts with a duplicate primary key are rejected, including keys duplicated within this batch. How many inserts are accepted?",
                 len(accepted), f"Accepted: {', '.join(map(str, accepted))}. Rejected: 200 and 100 (already present) and the second 500."))
    q.append(num(TX, 2, "Account A starts at 500. The log shows T1 adding 120 and committing, T2 subtracting 200 with no commit record, T3 subtracting 50 and committing, and T4 adding 75 and then aborting. After recovery keeps only committed effects, what is A?",
                 500 + 120 - 50, "Keep T1 and T3: 500 + 120 − 50 = 570. T2 never committed and T4 aborted."))
    q.append(num(MT, 2, "A shared counter starts at 1000. Eight threads each run a loop of two iterations; each iteration locks the same mutex, adds 25 and unlocks. What is the counter's final value?",
                 1000 + 8 * 2 * 25, "The mutex serializes all 16 increments: 1000 + 16 × 25 = 1400."))
    p3 = (47 % 11 + 3 * (1 + 47 % 7)) % 11
    q.append(num(HX7, 2, "A double-hashing table has m = 11 slots, h1(k) = k mod 11, h2(k) = 1 + (k mod 7) and p_i(k) = (h1(k) + i·h2(k)) mod 11 for i = 0, 1, 2, … For key 47, which slot is probe p_3 (the fourth probe)?",
                 p3, f"h1(47) = 3 and h2(47) = 1 + 5 = 6. p_3 = (3 + 3 × 6) mod 11 = 21 mod 11 = {p3}."))
    likes = [7, 3, 7, 9, 3, 7, 1]
    q.append(num(REL, 2, "Likes contains rows with PostID values 7, 3, 7, 9, 3, 7, 1. How many rows does SELECT PostID, COUNT(*) FROM Likes GROUP BY PostID return?",
                 len(set(likes)), "One row per distinct PostID: 1, 3, 7, 9, so 4 rows. Post 7's count is 3."))

    reqs = [("r", 3), ("r", 11), ("w", 19), ("w", 5), ("r", 13), ("r", 6), ("w", 14)]
    q.append(num(TS, 3, "A thread-safe hash index has capacity 8 and per-slot reader/writer locks. Each request locks slot key mod 8. All requests arrive in this order within one logical time step, and a granted lock is held for the whole step; a blocked request holds nothing. Reads share a slot; a write conflicts with any other request on its slot. Requests: read 3; read 11; write 19; write 5; read 13; read 6; write 14. How many requests proceed?",
                 sim.rw_proceed(8, reqs), "Slots: 3, 3, 3, 5, 5, 6, 6. Proceed: read 3, read 11 (shares slot 3), write 5, read 6. Blocked: write 19 (readers on slot 3), read 13 (writer on slot 5), write 14 (reader on slot 6). Total 4."))
    edges = [(1, 2), (3, 4), (2, 3), (5, 6), (6, 7), (7, 5), (8, 9), (9, 10)]
    q.append(num(MT, 3, "Eight transfers are ready, and each locks both accounts it touches: (1,2), (3,4), (2,3), (5,6), (6,7), (7,5), (8,9), (9,10). What is the largest number that can run at the same time without two transfers sharing an account?",
                 sim.max_disjoint(edges), "Chain 1–2–3–4 allows (1,2) and (3,4); triangle 5–6–7 allows one; chain 8–9–10 allows one. 2 + 1 + 1 = 4."))
    active, fields = [20, 12, 32, 5], 3
    ops = 4 * 32 + sum(active) * fields
    q.append(num(SP, 3, "An index builder scans 4 pages with MAX_SLOTS = 32. It checks every slot and deserializes 3 fields from each active tuple. The pages have 20, 12, 32 and 5 active slots. Counting each slot check and each field deserialization as one operation, how many operations are performed?",
                 ops, f"Slot checks: 4 × 32 = 128. Deserializations: ({' + '.join(map(str, active))}) × 3 = {sum(active)} × 3 = {sum(active) * 3}. Total = {ops}."))
    trace = [1, 2, 1, 3, 4, 5, 1, 6, 7, 1]
    lm, _ = sim.lru(3, trace)
    tm, _, _, _ = sim.twoq(3, trace)
    q.append(num(BM, 3, f"Compare LRU and 2Q, each with capacity 3 and starting empty, on the trace {', '.join(map(str, trace))}. Each miss causes one disk load. {TWOQ_RULES} How many disk loads does 2Q avoid relative to LRU?",
                 lm - tm, f"LRU: {lm} loads. 2Q: {tm} loads. Page 1 is promoted to LRU in 2Q and survives the scan of 3–7. Difference = {lm - tm}."))
    keys = [14, 24, 5, 34, 15, 4]
    slots = sim.linear_slots(10, keys)
    disp = [(slots[k] - k % 10) % 10 for k in keys]
    q.append(num(HX7, 3, "A ten-slot table starts empty and uses h(k) = k mod 10 with linear probing. Each entry also records its key's home slot, so its displacement is (slot − home) mod 10. Insert keys 14, 24, 5, 34, 15 and 4 in that order. What is the sum of the six keys' displacements?",
                 sum(disp), "Final slots: " + ", ".join(f"{k}→{slots[k]}" for k in keys) + f". Displacements: {', '.join(map(str, disp))}. Sum = {sum(disp)}."))
    return q


def exam3_numeric():
    q = []
    q.append(num(REL, 2, "Users holds UserIDs 1–5. Posts holds posts by users 2, 3 and 5, with Posts.UserID → Users.UserID declared ON DELETE RESTRICT. The system attempts to delete users 1, 2, 4, 5 and 6. A delete succeeds only if the user exists and no post references it. How many deletes succeed?",
                 2, "1 and 4 succeed. 2 and 5 are referenced (RESTRICT rejects them) and user 6 doesn't exist."))
    tuples = [300, 450, 120, 600]
    free = 4096 - 24 - len(tuples) * 8 - sum(tuples)
    q.append(num(SP, 2, "A 4096-byte slotted page has a 24-byte header. Each slot entry takes 8 bytes. Tuples of 300, 450, 120 and 600 bytes are inserted, each with its own new slot. How many bytes of free space remain?",
                 free, f"4096 − 24 − 4 × 8 − {sum(tuples)} = {free}."))
    q.append(num(HX, 2, "A 10-slot hash index uses h(key) = key mod 10 with linear probing. Lookups stop at a never-used slot and skip tombstones. An insert remembers the first tombstone, keeps probing for an existing copy of the key, and otherwise reuses that tombstone. Operations: insert 13; insert 23; insert 33; delete 23; insert 43. Which slot receives key 43?",
                 sim.linear_ops(10, [("ins", 13), ("ins", 23), ("ins", 33), ("del", 23), ("ins", 43)]),
                 "13 → 3, 23 → 4, 33 → 5. Deleting 23 leaves a tombstone at 4. Inserting 43 probes 3 (taken), 4 (tombstone, remembered), 5 (taken), 6 (never used, so 43 is absent) and reuses slot 4."))
    keys = [3, 18, 7, 21, 34, 11, 40]
    q.append(num(TS, 2, "A 16-slot hash index uses 4 lock stripes: key k goes to slot k mod 16, and slot s is protected by stripe s mod 4. Inserts take their stripe exclusively. In one time step, inserts for keys 3, 18, 7, 21, 34, 11 and 40 arrive in that order. An insert proceeds if its stripe is free; otherwise it blocks and holds nothing. How many inserts proceed?",
                 sim.rw_proceed(4, [("w", k) for k in keys]), "Slots: 3, 2, 7, 5, 2, 11, 8, so stripes: 3, 2, 3, 1, 2, 3, 0. Proceed: 3 (stripe 3), 18 (stripe 2), 21 (stripe 1), 40 (stripe 0). Blocked: 7, 34, 11. Total 4."))
    q.append(num(REL, 2, "Users has 4 rows. Posts has 9 rows, and every post's non-NULL UserID references an existing Users.UserID (the primary key). How many rows does the inner join Users ⋈ Posts on UserID produce?",
                 9, "Each post matches exactly one user, because the join is from a foreign key to a primary key, so the result has one row per post: 9."))

    trace = [4, 5, 4, 6, 7, 5, 8, 4, 9]
    _, ev, _, _ = sim.twoq(3, trace)
    q.append(num(BM, 3, f"A 2Q buffer with capacity 3 starts empty and processes the trace {', '.join(map(str, trace))}. {TWOQ_RULES} Which page is removed by the third eviction?",
                 ev[2], f"The evictions, in order, are pages {', '.join(map(str, ev))}."))
    keys = [7, 17, 27, 37, 47]
    slots, probes = sim.quadratic(10, keys)
    q.append(num(HX, 3, "A ten-slot table starts empty and uses h(k) = k mod 10 with quadratic probing p_i = (h(k) + i²) mod 10, for i = 0, 1, 2, … Insert keys 7, 17, 27, 37 and 47 in that order. How many slot probes do the five inserts perform in total?",
                 probes, "Final slots: " + ", ".join(f"{k}→{slots[k]}" for k in keys) + f". Probes per insert: 1, 2, 3, 4, 5, so {probes} in total."))
    q.append(num(TX, 3, "X starts at 800. Unsynchronized schedule: T1 reads 800 and computes X − 100; T2 reads 800 and computes X + 250; T2 writes 1050; T3 reads 1050 and computes X + 50; T1 writes its value; T3 writes its value. What is the final value of X?",
                 1100, "T1 writes 700, but T3 then writes 1050 + 50 = 1100, the last write. T1's update is lost."))
    accts = [1, 2, 1, 3, 1, 2]
    saved = len(accts) * 3 - max(accts.count(a) for a in set(accts)) * 3
    q.append(num(MT, 3, "Six account updates arrive together, touching accounts 1, 2, 1, 3, 1, 2. Each holds its critical section for 3 ms. With one global mutex they run strictly one after another. With one mutex per account, updates to different accounts overlap fully, but updates to the same account run one after another. How many milliseconds does per-account locking save?",
                 saved, f"Global: 6 × 3 = 18 ms. Per-account: account 1 has three updates, so 9 ms (the others finish within that). Saved = 18 − 9 = {saved}."))
    q.append(num(ST, 3, "A page on disk holds 20 tuples. Instance P loads it, inserts 4, deletes 1 and writes it back. Next, Q and R both load the page from disk. Q deletes 6 tuples and writes the page. Then R inserts 2 tuples into its own in-memory copy and writes the page. How many tuples does a new instance S read from disk?",
                 25, "P persists 20 + 4 − 1 = 23. Q and R both load 23. Q writes 17, but R's later write of 23 + 2 = 25 overwrites it. S reads 25."))
    return q


def exam4_numeric():
    q = []
    existing, ins, rejected = {5, 10, 15}, [10, 20, 20, 25, 5, 30], 0
    for k in ins:
        if k in existing:
            rejected += 1
        else:
            existing.add(k)
    q.append(num(REL, 2, "Users already contains primary keys {5, 10, 15}. The system tries to insert, in order, keys 10, 20, 20, 25, 5 and 30. Duplicate primary keys are rejected, including duplicates within this batch. How many inserts are rejected?",
                 rejected, "Rejected: 10 and 5 (already present) and the second 20. Total 3."))
    q.append(num(TX, 2, "A counter starts at 80. The log shows, in order: T1 adds 40 and commits; T2 doubles the counter and commits; T3 subtracts 100 with no commit record; T4 adds 10 and commits. Recovery applies only committed transactions, in log order. What is the final value?",
                 (80 + 40) * 2 + 10, "80 + 40 = 120. Doubling gives 240. T3 is removed. 240 + 10 = 250."))
    have, reqs, misses = {3, 6, 9, 12}, [6, 1, 3, 15, 1, 12, 20], []
    for r in reqs:
        if r not in have:
            misses.append(r)
            have.add(r)
    q.append(num(BM, 2, "A page map initially holds page ids 3, 6, 9 and 12. Requests arrive for 6, 1, 3, 15, 1, 12 and 20. Each miss reads one 4096-byte page and adds it to the map; nothing is evicted. How many bytes are read?",
                 len(misses) * 4096, f"Misses: {', '.join(map(str, misses))} (the second request for 1 is a hit). {len(misses)} × 4096 = {fmt(len(misses) * 4096)}."))
    ops = [("ins", 6), ("ins", 16), ("ins", 26), ("ins", 36), ("del", 16), ("del", 26)]
    q.append(num(HX7, 2, "A ten-slot table uses h(k) = k mod 10 with linear probing. Lookups skip tombstones and stop at the key or at a never-used slot. Operations: insert 6; insert 16; insert 26; insert 36; delete 16; delete 26. A lookup for key 46 (not present) follows. How many slots does that lookup examine, counting the never-used slot that ends it?",
                 sim.lookup_probes(10, ops, 46), "6, 16, 26, 36 fill slots 6–9. The deletes leave tombstones at 7 and 8. The lookup checks 6 (key 6), 7 (tombstone), 8 (tombstone), 9 (key 36), then 0 (never used): 5 slots."))
    pages = 67108864 // 4096
    bits = pages * 4
    q.append(num(SP, 2, "A database holds 64 MiB (67,108,864 bytes) of 4096-byte data pages. A free-space map stores 4 bits per data page, in 4096-byte pages, and tracks only data pages. How many pages does the free-space map occupy?",
                 -(-(bits // 8) // 4096), f"{fmt(pages)} data pages × 4 bits = {fmt(bits)} bits = {fmt(bits // 8)} bytes = 2 pages."))

    trace = [2, 4, 6, 2, 8, 4, 10, 2, 6]
    m, ev = sim.lru(3, trace)
    q.append(num(BM, 3, f"An LRU buffer with capacity 3 starts empty and processes the trace {', '.join(map(str, trace))}. Each miss reads one 8192-byte page, and every eviction writes one 8192-byte page. How many bytes are transferred in total?",
                 (m + len(ev)) * 8192, f"{m} misses and {len(ev)} evictions (evicted: {', '.join(map(str, ev))}). ({m} + {len(ev)}) × 8192 = {fmt((m + len(ev)) * 8192)}."))
    slots = sim.double_hash(11, [3, 14, 25, 36], lambda k: 1 + k % 5)
    q.append(num(HX, 3, "An 11-slot table starts empty and uses h1(k) = k mod 11, h2(k) = 1 + (k mod 5) and p_i(k) = (h1(k) + i·h2(k)) mod 11. Insert keys 3, 14, 25 and 36 in that order. Which slot does key 36 end up in?",
                 slots[36], "All four keys have h1 = 3. Final slots: " + ", ".join(f"{k}→{s}" for k, s in slots.items()) + "."))
    ops = [("d", 4), ("d", 9), ("d", 1), "ins", "ins", ("d", 6), "ins", "ins", "ins"]
    q.append(num(SP, 3, "A fixed-length record page starts with slots 0–11 occupied, free-list head = −1 and next_unused = 12. A delete pushes its slot onto the front of the free list. An insert takes the free-list head, or next_unused if the list is empty. Operations: delete 4; delete 9; delete 1; insert; insert; delete 6; insert; insert; insert. Which slot receives the final insert?",
                 sim.free_list(12, ops), "After the deletes the list is [1, 9, 4]. The inserts take 1, then 9. Delete 6 gives [6, 4]. The inserts take 6, then 4, and the last one uses next_unused = 12."))
    reqs = [("r", 4), ("w", 14), ("r", 24), ("r", 7), ("r", 17), ("w", 9), ("r", 19), ("w", 29)]
    q.append(num(TS, 3, "A thread-safe hash index has capacity 10 and per-slot reader/writer locks. Each request locks slot key mod 10. All requests arrive in this order within one logical time step, and a granted lock is held for the whole step; a blocked request holds nothing. Reads share a slot; a write conflicts with any other request on its slot. Requests: read 4; write 14; read 24; read 7; read 17; write 9; read 19; write 29. How many requests proceed?",
                 sim.rw_proceed(10, reqs), "Proceed: read 4, read 24 (the blocked write 14 holds nothing), read 7, read 17, write 9. Blocked: write 14, read 19, write 29. Total 5."))
    r, s = [2, 2, 2, 5, 5, 7, 9], [2, 5, 5, 5, 7, 7, 8]
    q.append(num(REL, 3, "Relation R has join-key values 2, 2, 2, 5, 5, 7, 9. Relation S has join-key values 2, 5, 5, 5, 7, 7, 8. How many rows does the inner join on R.K = S.K produce?",
                 sim.join_count(r, s), "Key 2: 3 × 1 = 3; key 5: 2 × 3 = 6; key 7: 1 × 2 = 2; keys 8 and 9 don't match. Total = 11."))
    return q


def exam5_numeric():
    q = []
    q.append(num(REL, 2, "Users contains UserIDs {1, 3, 5, 7}. Posts.UserID is a nullable foreign key referencing Users.UserID. Under standard SQL foreign-key semantics, the system inserts posts with UserID values 3, NULL, 4, 7, NULL and 9. How many inserts succeed?",
                 4, "A NULL foreign key isn't checked, so both NULLs succeed, along with 3 and 7. Only 4 and 9 fail: 4 succeed."))
    used, ok = 300, 0
    for t in [900, 700, 200, 150]:
        if used + t <= 2048:
            used += t
            ok += 1
    q.append(num(SP, 2, "A page has capacity 2048 bytes and starts with used_size = 300. Inserts of 900, 700, 200 and 150 bytes are attempted in that order. An insert succeeds only if the resulting used_size ≤ 2048; rejected inserts leave the page unchanged. How many inserts succeed?",
                 ok, "300 + 900 = 1200 succeeds, + 700 = 1900 succeeds, + 200 = 2100 is rejected, + 150 = 2050 is rejected. 2 succeed."))
    q.append(num(TX, 2, "A balance starts at 2000. Clerk 1 reads 2000 and plans to deposit 500. Clerk 2 reads 2000 and plans to withdraw 300. Clerk 1 writes 2500, then Clerk 2 writes 1700. By how many dollars does the final balance differ from the serial result?",
                 2200 - 1700, "Serial result: 2000 + 500 − 300 = 2200. The final balance is 1700, so the difference is 500. Clerk 1's deposit was lost."))
    q.append(num(HX, 2, "A 7-slot hash index uses h(key) = key mod 7 with linear probing. Lookups stop at a never-used slot and skip tombstones. An insert remembers the first tombstone, keeps probing for an existing copy of the key (updating it in place if found), and otherwise reuses that tombstone. Operations: insert 10; insert 17; insert 24; delete 17; insert 24 (new value). Which slot holds the result of the final insert?",
                 sim.linear_ops(7, [("ins", 10), ("ins", 17), ("ins", 24), ("del", 17), ("ins", 24)]),
                 "10 → 3, 17 → 4, 24 → 5. Deleting 17 leaves a tombstone at 4. The final insert probes 3 (10), 4 (tombstone, remembered), then 5, where it finds 24 and updates it in place. Slot 5."))
    q.append(num(MT, 2, "A counter starts at 0. Four threads each perform 250 mutex-protected increments, and two other threads each perform 100 mutex-protected decrements, all running concurrently. What is the final value?",
                 4 * 250 - 2 * 100, "The mutex keeps every update: 1000 − 200 = 800."))

    trace = [1, 2, 3, 1, 2, 4, 5, 6, 7, 1, 2, 8, 1]
    lm, _ = sim.lru(4, trace)
    tm, _, _, _ = sim.twoq(4, trace)
    q.append(num(BM, 3, f"Compare LRU and 2Q, each with capacity 4 and starting empty, on the trace {', '.join(map(str, trace))}. Each miss causes one disk load. {TWOQ_RULES} How many disk loads does 2Q avoid relative to LRU?",
                 lm - tm, f"LRU: {lm} loads. 2Q: {tm} loads. Pages 1 and 2 reach the LRU queue in 2Q and survive the scan of 4–8. Difference = {lm - tm}."))
    n_read, n_write, t = 10, 4, 3
    q.append(num(TS, 3, "A batch of 10 lookups and 4 inserts hits a hash index, and each operation holds its lock for 3 ms. Protocol A uses one global std::mutex, so all 14 operations run one at a time. Protocol B uses one global std::shared_mutex: assume all 10 lookups run together in a single shared phase, then each insert runs alone in exclusive mode. How many milliseconds does protocol B save over protocol A?",
                 (n_read + n_write) * t - (t + n_write * t), "A: 14 × 3 = 42 ms. B: one shared phase of 3 ms plus 4 × 3 = 12 ms of exclusive inserts = 15 ms. Saved = 42 − 15 = 27."))
    pages = 1073741824 // 4096
    nbytes = pages * 2 // 8
    q.append(num(SP, 3, "A database stores 1 GiB (1,073,741,824 bytes) of 4096-byte data pages. A two-bit free-space bitmap stores 2 bits per data page, in 4096-byte pages, and tracks only data pages. How many pages does the bitmap occupy?",
                 nbytes // 4096, f"{fmt(pages)} data pages × 2 bits = {fmt(pages * 2)} bits = {fmt(nbytes)} bytes. {fmt(nbytes)} / 4096 = {nbytes // 4096} pages."))
    c = 400
    c += c * 25 // 100
    c1 = c
    c *= 2
    c2 = c
    c += 30
    q.append(num(TX, 3, "A counter starts at 400. The log shows, in order: T1 adds 25% of the current value and commits; T2 subtracts 90 with no commit record; T3 doubles the counter and commits; T4 subtracts a quarter of the counter and aborts; T5 adds 30 and commits. Recovery applies only committed transactions, in log order, and percentages use integer division. What is the final value?",
                 c, f"T1: 400 + 100 = {c1}. T2 is removed. T3: {c1} × 2 = {c2}. T4 is removed. T5: {c2} + 30 = {c}."))
    active = [50, 0, 23, 41, 7]
    ops = 5 * 50 + sum(active) * 2
    q.append(num(SP, 3, "An index builder scans 5 pages with MAX_SLOTS = 50. It checks every slot and deserializes 2 fields from each active tuple. The pages have 50, 0, 23, 41 and 7 active slots. Counting each slot check and each field deserialization as one operation, how many operations are performed?",
                 ops, f"Slot checks: 5 × 50 = 250. Deserializations: {sum(active)} × 2 = {sum(active) * 2}. Total = {ops}."))
    return q


NUMERIC = [exam1_numeric(), exam2_numeric(), exam3_numeric(), exam4_numeric(), exam5_numeric()]


def module_tf():
    """The 20 module T/F questions from each of the five original exams, in exam order."""
    general = [THREADS[i] for i in THREADS_GENERAL_IDX]
    m8 = [dict(THREADS[i], topic=TS) for i in THREADS_INDEX_IDX] + HASH8
    # (pool, questions per original exam): 12 from Modules 1-6, 8 from Modules 7-8
    pools = [(RELATIONAL, 3), (ACID, 2), (STORAGE, 2), (SLOTTED, 2), (BUFFER, 2), (general, 1),
             (HASHING, 3), (HASH7, 2), (m8, 3)]
    out = []
    for e in range(5):
        block = []
        for pool, k in pools:
            assert len(pool) >= 5 * k
            block.extend(pool[e * k:(e + 1) * k])
        random.Random(6422 + e).shuffle(block)
        out.extend(block)
    return out


TOPIC_ORDER = [REL, TX, ST, SP, HX, TS, BM, MT]


def make_set(sid, title, parts):
    questions = []
    out_parts = []
    for name, note, qs in parts:
        start = len(questions) + 1
        for q in qs:
            q = {k: v for k, v in q.items() if k != "points"}
            q["n"] = len(questions) + 1
            questions.append(q)
        out_parts.append({"name": name, "note": note, "from": start, "to": len(questions)})
    return {"id": sid, "title": title, "parts": out_parts, "questions": questions}


def build():
    modules = module_tf()
    numeric = [q for exam in NUMERIC for q in exam]
    numeric.sort(key=lambda q: TOPIC_ORDER.index(q["topic"]))  # stable: keeps exam order within a topic
    num_parts = [(t, "Enter an exact whole number.", [q for q in numeric if q["topic"] == t])
                 for t in TOPIC_ORDER if any(q["topic"] == t for q in numeric)]
    paper_parts = [(p, PAPER_NOTES[p], [q for q in PAPERS if q["topic"] == p]) for p in (P1, P2, P3, P4)]
    return [
        make_set("modules", "Modules · True/False",
                 [("Modules 1–8 · True/False", "100 questions, mixed topics", modules)]),
        make_set("numeric", "Numeric", num_parts),
        make_set("papers", "Papers · True/False", paper_parts),
    ]


def check(sets):
    seen = set()
    modules, numeric, papers = sets
    assert len(modules["questions"]) == 100 and all(q["type"] == "tf" for q in modules["questions"])
    assert len(numeric["questions"]) == 50 and all(q["type"] == "num" for q in numeric["questions"])
    assert len(papers["questions"]) == 50 and all(q["type"] == "tf" for q in papers["questions"])
    for s in sets:
        for q in s["questions"]:
            assert q["text"] not in seen, q["text"]
            seen.add(q["text"])
        tfs = [q for q in s["questions"] if q["type"] == "tf"]
        if tfs:
            print(f"{s['title']}: {len(s['questions'])} questions, True={sum(q['answer'] for q in tfs)}")
        else:
            print(f"{s['title']}: {len(s['questions'])} questions")
    for p in (P1, P2, P3, P4):
        qs = [q for q in papers["questions"] if q["topic"] == p]
        trues = sum(q["answer"] for q in qs)
        assert 5 <= trues <= len(qs) - 5, (p, trues, len(qs))
        print(f"  {p}: {len(qs)} questions, True={trues}")


if __name__ == "__main__":
    sets = build()
    check(sets)
    out = ROOT / "data" / "sets.js"
    out.write_text("// Generated by tools/build.py. Do not edit by hand.\nwindow.SETS = "
                   + json.dumps(sets, ensure_ascii=False, indent=1) + ";\n")
    print("wrote", out.relative_to(ROOT))
