"""Builds data/exams.js. Numeric answer keys come from sim.py, never from hand arithmetic.

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
    tf(TX, True, "Rewriting a data file by writing a temporary file and then atomically renaming it over the original means readers see either the old file or the new file, never a partial one.",
       "rename within one directory is atomic, so the switch from old file to new file happens in a single step."),
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

HX = "Hash indexing"
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

# ---------------------------------------------------------------------------
# Paper true/false (5 per exam)
# ---------------------------------------------------------------------------
P1, P2, P3, P4 = ("Codd 1970", "Stonebraker & Pavlo 2024", "Stonebraker 1981", "Umbra 2020")
PAPERS = [
    [
        tf(P1, True, "Codd warns that programs relying on a file's stored record order can fail when that order must change, because systems of his time didn't separate presentation order from stored order.",
           "This is the ordering dependence in §1.2.1."),
        tf(P1, False, "Codd defines a foreign key as a domain that must reference the primary key of a different relation; a relation can't reference its own primary key.",
           "Codd explicitly says the referenced relation S may be the same as R."),
        tf(P2, False, "Stonebraker and Pavlo argue that key/value stores are easy to re-engineer into systems with richer data models, whereas relational DBMSs struggle to emulate key/value stores.",
           "It's the reverse. Re-engineering a KV store for a complex data model is non-trivial, while an RDBMS emulates a KV store without changes."),
        tf(P3, True, "Stonebraker says LRU suits random accesses with a nonzero chance of re-reference, but for cyclic sequential access it is the worst possible policy unless all the pages fit in the cache.",
           "For cyclic patterns he recommends toss-immediately, and LRU for the random-with-reuse class."),
        tf(P4, False, "Umbra's B+-tree leaves keep sibling pointers so that table scans can move from leaf to leaf without revisiting inner nodes.",
           "Each page must have exactly one owning swip, so leaves have no sibling links. Scans keep an optimistic latch on the parent instead."),
    ],
    [
        tf(P1, True, "Codd's normalization removes nonsimple domains by copying the parent relation's primary key into each subordinate relation, and that copied key becomes part of the subordinate relation's key.",
           "§1.4: each expanded relation's key is its own key plus the parent key copied down."),
        tf(P2, True, "Stonebraker and Pavlo describe vector databases as essentially document-oriented DBMSs with specialized approximate-nearest-neighbor indexes.",
           "They call ANN indexes 'a feature, not the foundation of a new system architecture'."),
        tf(P2, False, "Stonebraker and Pavlo predict that shared-nothing architectures will return to dominate cloud DBMS design.",
           "They expect shared-disk designs on disaggregated storage to dominate, and don't foresee shared-nothing resurfacing."),
        tf(P3, False, "In the intentions-list recovery scheme Stonebraker describes, the page holding the commit flag must be forced to disk before the pages of the intentions list.",
           "It's the opposite: the commit-flag page must be forced after every intentions-list page."),
        tf(P4, True, "Umbra's smallest page size is 64 KiB, and each larger size class doubles the page size of the previous one.",
           "Size class i + 1 pages are twice as large as size class i pages."),
    ],
    [
        tf(P1, False, "Codd argues that following every supplier → part → project link always yields exactly the set of projects each supplier supplies.",
           "That's the 'connection trap'. Path following gives the true relation only if it happens to be the natural composition, for all time."),
        tf(P2, True, "Stonebraker and Pavlo note that data lakes can lack statistics on newly ingested files, which makes adaptive query processing important.",
           "Without statistics, the plan may need to adapt during execution."),
        tf(P3, False, "Stonebraker reports that UNIX could prefetch INGRES's next block correctly, because INGRES always reads the next block in logical file order.",
           "INGRES knows its next block, but that block often isn't the next one in file order, so the OS can't prefetch correctly."),
        tf(P3, True, "Stonebraker describes a convoy: if the OS deschedules a DBMS process while it holds a short-term lock on a shared resource, other processes quickly queue behind that lock.",
           "This is one of his two problems with the process-per-user model."),
        tf(P4, False, "Umbra's optimistic latch mode increments a reader count stored inside the latch word.",
           "Optimistic mode only remembers the version counter and doesn't modify the latch, so it causes no contention. Shared mode is the one that counts readers."),
    ],
    [
        tf(P1, False, "Codd says the universality of his proposed data sublanguage lies in its computing power: it can express any computable function.",
           "He says its universality lies in its descriptive ability, not its computing ability."),
        tf(P1, True, "Codd notes that strongly redundant relations may be kept deliberately, for example so old programs that refer to semi-obsolete relations by name keep running.",
           "§2.2.1 gives user convenience, including keeping old programs working, as a reason for strong redundancy."),
        tf(P2, False, "Stonebraker and Pavlo argue that relational DBMSs can't represent graphs, so graph workloads require native graph DBMSs.",
           "Graphs fit into Node and Edge tables, and SQL:2023 added property-graph queries (SQL/PGQ)."),
        tf(P3, True, "Stonebraker points out that mapping a 100 MB file into paged virtual memory needs about 100 KB of page table, which may not stay resident and can cause an extra page fault.",
           "At 4 bytes per 4 KB page, a non-resident page table can cost one fault for the table and another for the data."),
        tf(P4, True, "When Umbra evicts a page, it writes changes back with pwrite if needed and then uses madvise(MADV_DONTNEED) so the kernel can reclaim the physical memory, while the frame's virtual address stays reserved.",
           "That keeps physical memory use within the pool size even though far more virtual memory is reserved."),
    ],
    [
        tf(P1, True, "Codd treats consistency as a property of the database's current state, regardless of how that state came about.",
           "§2.3 makes no distinction between inconsistency caused by omission and inconsistency caused by commission."),
        tf(P2, False, "Stonebraker and Pavlo say NewSQL vendors correctly predicted that in-memory DBMSs would be widely adopted over the following decade.",
           "They say vendors incorrectly anticipated in-memory adoption: flash got cheaper and faster while DRAM stayed expensive."),
        tf(P2, True, "Stonebraker and Pavlo call blockchain databases an inefficient technology looking for an application.",
           "They note legitimate businesses won't pay a performance cost of about five orders of magnitude."),
        tf(P3, False, "Stonebraker concludes that a single-server DBMS process avoids duplicating operating-system facilities.",
           "A server model must do its own scheduling and multitasking, a 'painful duplication of operating system facilities'."),
        tf(P4, False, "Umbra freely reuses the disk space of one large deleted page for several smaller pages.",
           "Umbra reuses disk space only for pages of the same size. Otherwise ARIES could read stale bytes as a page's log sequence number after a crash."),
    ],
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
    total = 180 * 100 + 20 * 50000
    q.append(num(ST, 2, "A workload performs 200 page accesses. 180 are served from DRAM at 100 ns each and 20 from an SSD at 50,000 ns each. What is the average service time per access, in nanoseconds?",
                 total // 200, f"Total = 180 × 100 + 20 × 50,000 = {fmt(total)} ns. {fmt(total)} / 200 = {fmt(total // 200)} ns."))

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
    q.append(num(SP, 2, "A file of fixed-size pages is 1,310,720 bytes long and PAGE_SIZE = 4096. Pages are numbered from 0. What is the page id of the last page?",
                 1310720 // 4096 - 1, "num_pages = 1,310,720 / 4096 = 320, so ids run 0–319."))
    likes = [7, 3, 7, 9, 3, 7, 1]
    q.append(num(REL, 2, "Likes contains rows with PostID values 7, 3, 7, 9, 3, 7, 1. How many rows does SELECT PostID, COUNT(*) FROM Likes GROUP BY PostID return?",
                 len(set(likes)), "One row per distinct PostID: 1, 3, 7, 9, so 4 rows. Post 7's count is 3."))

    reqs = [("r", 3), ("r", 11), ("w", 19), ("w", 5), ("r", 13), ("r", 6), ("w", 14)]
    q.append(num(MT, 3, "Capacity 8. Each request locks slot key mod 8. All requests arrive in this order within one logical time step, and a granted lock is held for the whole step; a blocked request holds nothing. Reads share a slot; a write conflicts with any other request on its slot. Requests: read 3; read 11; write 19; write 5; read 13; read 6; write 14. How many requests proceed?",
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
    b = 2500
    b -= b * 12 // 100
    b1 = b
    b += 340
    b2 = b
    b -= b // 3
    q.append(num(TX, 3, "An account starts at 2500. Three isolated transactions run serially: T1 withdraws 12% of the current balance, T2 deposits 340, and T3 withdraws one third of the current balance. Percentages and fractions use integer division (the amount withdrawn is rounded down). What is the final balance?",
                 b, f"T1: 2500 − 300 = {b1}. T2: {b1} + 340 = {b2}. T3: {b2} − {b2 // 3} = {b}."))
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
    q.append(num(MT, 2, "A parallel index build scans 47 pages with 6 workers. Each of the first five workers receives floor(47 / 6) pages, and the last worker receives the rest. How many more pages does the last worker scan than worker 0?",
                 (47 - 5 * (47 // 6)) - 47 // 6, "floor(47/6) = 7. The last worker gets 47 − 35 = 12. 12 − 7 = 5."))
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
    total = 950 * 80 + 50 * 20000
    q.append(num(ST, 2, "1000 page accesses have a 95% buffer hit rate. Hits cost 80 ns from DRAM; misses cost 20,000 ns from SSD. What is the average access time in nanoseconds?",
                 total // 1000, f"950 × 80 + 50 × 20,000 = {fmt(total)} ns. {fmt(total)} / 1000 = {total // 1000} ns."))
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
    q.append(num(MT, 3, "Capacity 10. Each request locks slot key mod 10. All requests arrive in this order within one logical time step, and a granted lock is held for the whole step; a blocked request holds nothing. Reads share a slot; a write conflicts with any other request on its slot. Requests: read 4; write 14; read 24; read 7; read 17; write 9; read 19; write 29. How many requests proceed?",
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
    edges = [(1, 2), (2, 3), (3, 4), (4, 1), (5, 6), (7, 8), (8, 9), (9, 7), (10, 11)]
    q.append(num(MT, 3, "Nine transfers are ready, and each locks both accounts it touches: (1,2), (2,3), (3,4), (4,1), (5,6), (7,8), (8,9), (9,7), (10,11). What is the largest number that can run at the same time without two transfers sharing an account?",
                 sim.max_disjoint(edges), "Cycle 1–2–3–4 allows 2 ((1,2) and (3,4)); (5,6) allows 1; triangle 7–8–9 allows 1; (10,11) allows 1. Total 5."))
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

ACK = {
    "type": "ack",
    "topic": "Acknowledgement",
    "points": 0,
    "text": "You've reached the final zero-point acknowledgement question. Before submitting, show both sides of your scratch paper to the camera. Have you shown both sides of your scratch paper to the camera?",
    "answer": "Yes",
    "why": "On the real exam, answer Yes after showing the camera both sides of your scratch paper.",
}


def build():
    pools = [RELATIONAL, ACID, STORAGE, SLOTTED, HASHING, BUFFER, THREADS]
    exams = []
    for e in range(5):
        module = []
        for pool in pools:
            k = len(pool) // 5
            module.extend(pool[e * k:(e + 1) * k])
        random.Random(6422 + e).shuffle(module)
        for q in module:
            q["points"] = 1
        papers = [dict(q, points=1) for q in PAPERS[e]]
        questions = module + NUMERIC[e] + papers + [ACK]
        for i, q in enumerate(questions, 1):
            q["n"] = i
        exams.append({"id": e + 1, "title": f"Mock Exam {e + 1}", "questions": questions})
    return exams


def check(exams):
    seen = set()
    for ex in exams:
        qs = ex["questions"]
        tfs = [q for q in qs if q["type"] == "tf"]
        nums = [q for q in qs if q["type"] == "num"]
        assert len(qs) == 36 and len(tfs) == 25 and len(nums) == 10
        assert sum(q["topic"] in (P1, P2, P3, P4) for q in tfs) == 5
        assert sum(q["points"] for q in qs) == 50, ex["title"]
        assert [q["points"] for q in nums] == [2] * 5 + [3] * 5
        trues = sum(q["answer"] for q in tfs)
        assert 10 <= trues <= 15, (ex["title"], trues)
        for q in qs:
            if q["type"] != "ack":
                assert q["text"] not in seen, q["text"]
                seen.add(q["text"])
        print(f"{ex['title']}: 35 graded + ack, 50 pts, T/F true={trues}/25")


if __name__ == "__main__":
    exams = build()
    check(exams)
    out = ROOT / "data" / "exams.js"
    out.write_text("// Generated by tools/build.py. Do not edit by hand.\nwindow.EXAMS = "
                   + json.dumps(exams, ensure_ascii=False, indent=1) + ";\n")
    print("wrote", out.relative_to(ROOT))
